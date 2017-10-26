local _M = {}

local lrucache = require "resty.lrucache"
local c, err = lrucache.new(1000)
if not c then
    return error("failed to create the cache: " .. (err or "unknown"))
end

function _M.get_proxy_path(redis_url, sentinels)
    local regex = "^/(tenders|esco-tenders)/([0-9a-zA-Z_]+)/(.+)$"
    local match = ngx.re.match(ngx.var.uri, regex)
    local proxy_pass_value_cache, stale_data = c:get(match[2])

    if proxy_pass_value_cache then
        ngx.var.target = proxy_pass_value_cache;
    else
        local rc = require("resty.redis.connector").new()
        local redis, err = rc:connect({url = redis_url,sentinels = sentinels})
        if err then
            ngx.log(ngx.ERR, "redis: " .. (err or "unknown"))
            return ngx.exit(ngx.HTTP_METHOD_NOT_IMPLEMENTED)
        end

        local proxy_pass_value_redis, err = redis:get(match[2])
        if err or proxy_pass_value_redis == ngx.null then
            -- IF LOGIN THEN REDIRECT
            if match[3] == "login" then
                local args = ngx.req.get_uri_args()
                args["wait"] = "1"
                ngx.redirect("/" .. match[1] .. "/" .. match[2] .. "?" .. ngx.encode_args(args))
            end
            return ngx.exit(ngx.HTTP_NOT_FOUND)

        else
            -- Traling endslash
            local end_slash_index = proxy_pass_value_redis:match'^.*()/$'
            if end_slash_index != nil then
               proxy_pass_value_redis = string.sub(proxy_pass_value_redis, 0, end_slash_index -1 )
            end
            ngx.var.target = proxy_pass_value_redis
            -- Cache on 60 sec
            c:set(match[2], ngx.var.target, 60)
        end
    end

    ngx.req.set_header("X-Forwarded-Path", ngx.var.scheme .. "://" .. ngx.var.http_host .. ngx.var.uri)
    ngx.req.set_uri("/" .. match[3])

end

return _M