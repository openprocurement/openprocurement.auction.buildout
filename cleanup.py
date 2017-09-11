import consul

c = consul.Consul()

for i in c.session.list()[1]:
    if i['Name'] == '':
        c.session.destroy(i['ID'])
