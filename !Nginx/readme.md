# Nginx

> **Nginx** (pronounced "engine-x") is a high-performance, open-source web server, reverse proxy, load balancer, HTTP cache, and mail proxy server. Originally created by Igor Sysoev in 2004, it is widely used for serving static content, proxying requests, and handling large numbers of concurrent connections efficiently.
>
> ---
>
> ## Features
>
> - **High Performance & Concurrency** — Uses an event-driven, asynchronous, non-blocking architecture to handle thousands of simultaneous connections with low memory usage.
> - - **Reverse Proxy** — Forwards client requests to backend servers (Node.js, Python, PHP, etc.) and returns responses to clients.
>   - - **Load Balancing** — Distributes incoming traffic across multiple backend servers using round-robin, least connections, IP hash, or weighted strategies.
>     - - **Static File Serving** — Extremely fast at serving static files (HTML, CSS, JS, images, videos) directly from disk.
>       - - **SSL/TLS Termination** — Handles HTTPS encryption/decryption, offloading that work from backend servers.
>         - - **HTTP/2 & HTTP/3 Support** — Supports modern HTTP protocols for improved performance.
>           - - **URL Rewriting & Redirects** — Powerful `rewrite` and `return` directives for URL manipulation.
>             - - **Gzip/Brotli Compression** — Compresses responses to reduce bandwidth and improve page load times.
>               - - **Caching** — Built-in proxy caching to reduce load on upstream servers.
>                 - - **Rate Limiting** — Controls request rates to protect against abuse and DDoS.
>                   - - **Access Control** — IP allowlisting/blocklisting, HTTP Basic Auth, and JWT authentication (via OpenID Connect module).
>                     - - **WebSocket Proxying** — Supports proxying WebSocket connections.
>                       - - **Virtual Hosting** — Hosts multiple domains/sites on a single server using `server` blocks.
>                         - - **Health Checks** — Active and passive health checks for upstream servers (NGINX Plus).
>                           - - **Mail Proxy** — Supports IMAP, POP3, and SMTP proxying.
>                             - - **Modular Architecture** — Extend functionality with modules (Lua, GeoIP, ModSecurity WAF, etc.).
>                               - - **Cross-Platform** — Runs on Linux, macOS, Windows, and BSD.
>                                
>                                 - ---
>
> ## Notes
>
> ### Installation
>
> <details>
  <summary>Install on Ubuntu/Debian</summary>summary>
  
  ```bash
sudo apt update
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

</details>

<details>
  <summary>Install on CentOS/RHEL/Amazon Linux</summary>summary>

  ```bash
sudo yum install epel-release -y
sudo yum install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

</details>

<details>
  <summary>Install via Docker</summary>summary>

  ```bash
# Run nginx container serving files from current directory
docker run -d -p 80:80 --name mynginx nginx

# Run with custom config
docker run -d -p 80:80 \
  -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v $(pwd)/html:/usr/share/nginx/html:ro \
  --name mynginx nginx
```

</details>

---

### Configuration File Structure

The main config file is at `/etc/nginx/nginx.conf`. Site configs live in `/etc/nginx/conf.d/` or `/etc/nginx/sites-available/` (Debian/Ubuntu).

```
/etc/nginx/
├── nginx.conf              # Main config file
├── conf.d/                 # Drop-in config files (*.conf)
│   └── default.conf
├── sites-available/        # Available site configs (Debian/Ubuntu)
├── sites-enabled/          # Symlinks to enabled sites
├── snippets/               # Reusable config snippets
└── modules-enabled/        # Enabled dynamic modules
```

<details>
<summary>nginx.conf skeleton / structure overview</summary>summary>

  ```nginx
  # Global context
user  nginx;
worker_processes  auto;          # Usually set to number of CPU cores
error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;    # Max simultaneous connections per worker
    use epoll;                   # Efficient I/O method (Linux)
    multi_accept on;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    # Include virtual host configs
        include /etc/nginx/conf.d/*.conf;
}
```

</details>

---

### Serving Static Files

<details>
<summary>Basic static file server</summary>summary>

```nginx
server {
    listen 80;
    server_name example.com www.example.com;

    root /var/www/html;
    index index.html index.htm;

    location / {
        try_files $uri $uri/ =404;
    }

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff2)$ {
            expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

</details>

---

### Reverse Proxy

<details>
<summary>Reverse proxy to a Node.js / Python app</summary>summary>

  ```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:3000;   # Backend app address

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

</details>

<details>
<summary>Reverse proxy with upstream block (named backend)</summary>summary>

```nginx
upstream backend {
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
}

server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

</details>

---

### Load Balancing

<details>
  <summary>Round-robin (default)</summary>summary>

  ```nginx
  upstream myapp {
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
}
```

</details>

<details>
  <summary>Least connections</summary>summary>

  ```nginx
upstream myapp {
    least_conn;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
    }
```

</details>

<details>
  <summary>IP Hash (sticky sessions)</summary>summary>

  ```nginx
upstream myapp {
    ip_hash;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
}
```

</details>

<details>
  <summary>Weighted load balancing</summary>summary>

  ```nginx
upstream myapp {
    server 10.0.0.1:8080 weight=3;   # Gets 3x more traffic
    server 10.0.0.2:8080 weight=1;
        server 10.0.0.3:8080 backup;     # Only used if others are down
}
```

</details>

---

### SSL / HTTPS

<details>
  <summary>HTTPS with Let's Encrypt (Certbot)</summary>summary>

  ```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain and auto-configure cert
sudo certbot --nginx -d example.com -d www.example.com

# Renew certs (add to cron or systemd timer)
sudo certbot renew --dry-run
```

</details>

<details>
  <summary>Manual HTTPS server block</summary>summary>

  ```nginx
  server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}
```

</details>

---

### URL Rewrites & Redirects

<details>
  <summary>301 / 302 redirects</summary>summary>

  ```nginx
# Permanent redirect (301)
server {
    listen 80;
    server_name old.example.com;
    return 301 https://new.example.com$request_uri;
}

# Redirect a specific path
location /old-page {
    return 301 /new-page;
    }

# Temporary redirect (302)
location /sale {
    return 302 /promotions;
}
```

</details>

<details>
<summary>Rewrite rules</summary>summary>

  ```nginx
# Remove trailing slash
rewrite ^/(.*)/$ /$1 permanent;

# Rewrite /api/v1/... to /api/...
rewrite ^/api/v1/(.*)$ /api/$1 last;

# Redirect .php extension to clean URL
rewrite ^/(.*)\.php$ /$1 permanent;
```

</details>

---

### Gzip Compression

<details>
<summary>Enable Gzip compression</summary>

```nginx
http {
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
                application/json
        application/xml
        image/svg+xml
        font/woff
                font/woff2;
}
```

</details>

---

### Caching

<details>
  <summary>Proxy cache setup</summary>summary>

  ```nginx
http {
    # Define a cache zone (100MB on disk, 10MB for keys)
    proxy_cache_path /var/cache/nginx levels=1:2
                     keys_zone=my_cache:10m
                     max_size=100m
                                          inactive=60m
                     use_temp_path=off;

    server {
        listen 80;
        server_name example.com;

        location / {
            proxy_cache my_cache;
            proxy_cache_valid 200 1d;
            proxy_cache_valid 404 1m;
            proxy_cache_use_stale error timeout updating;
                        add_header X-Cache-Status $upstream_cache_status;

            proxy_pass http://backend;
        }
    }
}
```

</details>

---

### Rate Limiting

<details>
<summary>Limit requests per second</summary>

  ```nginx
http {
    # Define limit zone: 10MB storage, 10 req/sec per IP
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name api.example.com;

        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            limit_req_status 429;

            proxy_pass http://backend;
        }
    }
}
```

</details>

---

### WebSocket Proxying

<details>
  <summary>Proxy WebSocket connections</summary>summary>

  ```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 80;
    server_name ws.example.com;

    location /ws/ {
        proxy_pass http://127.0.0.1:4000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }
}
```

</details>

---

### Basic Authentication

<details>
  <summary>Protect a location with HTTP Basic Auth</summary>summary>

  ```bash
# Install htpasswd utility
sudo apt install apache2-utils -y

# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

```nginx
server {
    listen 80;
    server_name internal.example.com;

    location /admin/ {
        auth_basic "Restricted Area";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass http://127.0.0.1:3000;
    }
}
```

</details>

---

### Access Control (IP Allowlist / Blocklist)

<details>
<summary>Allow/deny by IP address</summary>summary>

  ```nginx
location /admin {
    allow 192.168.1.0/24;   # Allow local network
    allow 10.0.0.5;          # Allow specific IP
    deny all;                # Block everyone else
}
```

</details>

---

### Security Headers

<details>
  <summary>Add common security headers</summary>summary>

  ```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Hide nginx version
    server_tokens off;
}
```

</details>

---

### Custom Error Pages

<details>
  <summary>Custom 404 and 50x error pages</summary>summary>

  ```nginx
  server {
      listen 80;
    server_name example.com;
    root /var/www/html;

    error_page 404 /404.html;
    location = /404.html {
        internal;
    }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
            internal;
                }
}
```

</details>

---

### Logging

<details>
  <summary>Custom log format and access logs</summary>summary>

  ```nginx
http {
    log_format main '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    'rt=$request_time uct=$upstream_connect_time '
                    'uht=$upstream_header_time urt=$upstream_response_time';

    access_log /var/log/nginx/access.log main;
    error_log  /var/log/nginx/error.log warn;

    server {
        # Disable access log for static assets (performance)
        location ~* \.(css|js|jpg|png|gif|ico|woff2)$ {
            access_log off;
        }
    }
}
```

</details>

---

### Useful CLI Commands

<details>
<summary>Nginx CLI reference</summary>

  ```bash
# Test configuration syntax
sudo nginx -t

# Reload config without downtime
sudo nginx -s reload

# Stop nginx gracefully
sudo nginx -s quit

# Stop nginx immediately
sudo nginx -s stop

# Start nginx
sudo systemctl start nginx

# Check nginx status
sudo systemctl status nginx

# View error log live
sudo tail -f /var/log/nginx/error.log

# View access log live
sudo tail -f /var/log/nginx/access.log

# Print nginx version and compile options
nginx -V

# Show which config file is being used
nginx -t 2>&1 | head -1
```

</details>

---

### Tips & Best Practices

- **Always run `sudo nginx -t`** before reloading to catch config errors.
- - Use **`include` directives** to split configs into logical files per site or feature.
  - - Set `worker_processes auto;` to automatically use all available CPU cores.
    - - Use **`try_files $uri $uri/ =404;`** for single-page apps (SPA) to handle client-side routing.
    - Set **`keepalive_timeout 65;`** and **`keepalive_requests 100;`** to reduce TCP handshake overhead.
    - - Enable **`sendfile on;`** and **`tcp_nopush on;`** for efficient static file serving.
      - - Use **upstream `keepalive`** connections to reuse backend connections:
        -   ```nginx
              upstream backend {
                  server 127.0.0.1:3000;      keepalive 32;  }  ```
                  - Store certs in `/etc/letsencrypt/` and automate renewal via a systemd timer or cron.
            - Use `$binary_remote_addr` instead of `$remote_addr` in rate-limit zones to save memory.

            ---

            ## References

            - [Nginx Official Documentation](https://nginx.org/en/docs/)
            - [Nginx Beginner's Guide](https://nginx.org/en/docs/beginners_guide.html)
            - [Nginx Admin Guide](https://docs.nginx.com/nginx/admin-guide/)
            - [Nginx Config Generator (digitalocean)](https://www.digitalocean.com/community/tools/nginx)
            - [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
            - [Nginx Cookbook (O'Reilly free edition)](https://www.nginx.com/resources/library/complete-nginx-cookbook/)
            - [Awesome Nginx](https://github.com/agile6v/awesome-nginx)
</summary>
</details>
