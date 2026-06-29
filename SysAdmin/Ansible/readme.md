# Ansible

> [!NOTE]   
> **Status**: In Progress
---

## Notes

### Inventory

<details><summary>Sample Inventory File</summary>

```
# Web Servers
web_node1 ansible_host=web01.xyz.com ansible_connection=winrm ansible_user=administrator ansible_password=Win$Pass
web_node2 ansible_host=web02.xyz.com ansible_connection=winrm ansible_user=administrator ansible_password=Win$Pass
web_node3 ansible_host=web03.xyz.com ansible_connection=winrm ansible_user=administrator ansible_password=Win$Pass

# DB Servers
sql_db1 ansible_host=sql01.xyz.com ansible_connection=ssh ansible_user=root ansible_ssh_pass=Lin$Pass
sql_db2 ansible_host=sql02.xyz.com ansible_connection=ssh ansible_user=root ansible_ssh_pass=Lin$Pass

[db_nodes]
sql_db1
sql_db2

[web_nodes]
web_node1
web_node2
web_node3

[boston_nodes]
sql_db1
web_node1

[dallas_nodes]
sql_db2
web_node2
web_node3

[us_nodes:children]
boston_nodes
dallas_nodes
```
</details>

### Variables
- Variable precedence
- Magic variables
- Facts
    - playbook
        gather_facts: no
    - /etc/ansible/ansible.cfg
        gathering = implicit
        or
        gathering = explicit

<details><summary>Sample variables</summary>

```
```
</details>

### Playbooks
### Handlers, Roles, Collections
### Advanced topics
<details><summary>Example: Jinja2 Templates for Dynamic Configs</summary>

- `/etc/ansible/hosts`
```bash
[web_servers]
web1 ansible_host=172.20.1.100
web2 ansible_host=172.20.1.101
web3 ansible_host=172.20.1.102
```

- `playbook.yaml`
```bash
-
    hosts: web_servers
    tasks:
        - name: Copy index.html to remote servers
          template:
            src: index.html.j2
            dest: /var/www/nginx-default/index.html
```

- `index.html.j2`
```html
<!DOCTYPE html>
<html>
<body>

This is {{inventory_hostname }} Server

</body>
</html>
``` 
</details>

## References