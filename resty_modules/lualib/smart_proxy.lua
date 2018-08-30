-- Documentation:
-- https://github.com/openresty/lua-nginx-module
-- https://github.com/openresty/lua-resty-redis
-- https://openresty-reference.readthedocs.io/en/latest/Lua_Nginx_API/

local _M = {}

local lrucache = require("resty.lrucache")
local cache, err = lrucache.new(1000)
if not cache then
    return error("failed to create the cache: " .. (err or "unknown"))
end

function _M.get_proxy_path(protocol, redis_url, sentinels)
    -- Uncomment the following line to enable debugging headers
    --ngx.header["X-Smart-Proxy-Debug"] = {ngx.var[1], ngx.var[2], ngx.var[3]}

    local resource_id = ngx.var[1]
    local pass_uri = ngx.var[2]

    -- Try to get the target for the nginx's proxy_pass directive from the LRU cache
    local proxy_pass_value_cache, stale_data = cache:get(resource_id)

    if proxy_pass_value_cache then
        -- Entry found in cache, no need for querying Redis
        ngx.var.target = proxy_pass_value_cache
    else
        -- If the cache does not contain the entry we were looking for,
        -- commence connecting to Redis.
        local rc = require("resty.redis.connector").new()
        local redis, err = rc:connect({url = redis_url,sentinels = sentinels})
        if err then
            ngx.log(ngx.ERR, "redis: " .. (err or "unknown"))
            return ngx.exit(ngx.HTTP_METHOD_NOT_IMPLEMENTED)
        end

        -- Try to get the target by querying Redis.
        -- Here the tender ID is a key of an entry in Redis,
        -- and its corresponding value is the target for proxy_pass.
        local proxy_pass_value_redis, err = redis:get(resource_id)

        if err or proxy_pass_value_redis == ngx.null then
            -- If there is no such key in Redis or in case of some error,
            -- check the trailing part of the URI.
            if pass_uri == "login" then
                -- If that part is "login", redirect the client to the same URI
                -- with a "wait=1" parameter appended.
                local args = ngx.req.get_uri_args()
                args["wait"] = "1"
                ngx.redirect("/auctions/" .. resource_id .. "?" .. ngx.encode_args(args))
            end
            -- Return 404 if pass_uri is not known
            return ngx.exit(ngx.HTTP_NOT_FOUND)
        else
            -- Determine the presence of a trailing slash
            if proxy_pass_value_redis:sub(-1) == '/' then
               -- The following line will strip only one last character and not two,
               -- since this is how indexes work in Lua.
               proxy_pass_value_redis = proxy_pass_value_redis:sub(0, -2)
            end
            ngx.var.target = proxy_pass_value_redis
            -- Keep the entry in the LRU cache for 60 seconds
            cache:set(resource_id, ngx.var.target, 60)
        end
    end

    ngx.req.set_header("X-Forwarded-Path", protocol .. "://" .. ngx.var.http_host .. ngx.var.uri)
    ngx.req.set_uri("/" .. pass_uri)
end

return _M
