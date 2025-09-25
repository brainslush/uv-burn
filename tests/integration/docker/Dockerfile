FROM nginx:1.27-alpine

# Install the tool just to generate htpasswd (will remain in final image)
RUN apk add --no-cache apache2-utils

# Create htpasswd with hardcoded credentials user1:pass1
RUN mkdir -p /etc/nginx/auth \
    && htpasswd -b -c /etc/nginx/auth/pypi.htpasswd userfoo passbar

# Copy Nginx config (listens on port 80 inside container)
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
