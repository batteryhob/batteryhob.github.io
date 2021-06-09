FROM batteryho/jekyll-custom:latest
COPY . /srv/jekyll

EXPOSE 4000

ENTRYPOINT [ "jekyll", "serve", "--force_polling", "--trace" ]