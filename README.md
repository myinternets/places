# Places

**Places is an experimental project, use at your own risks**

[![Tests](https://github.com/myinternets/places/actions/workflows/test.yml/badge.svg?event=push)](https://github.com/myinternets/places/actions/workflows/ruff.yml)

[![Docker Image CI](https://github.com/myinternets/places/actions/workflows/docker-image.yml/badge.svg)](https://github.com/myinternets/places/actions/workflows/docker-image.yml)

_Semantic Search on your Browser History._

Finding data back into your browsing history is hard with the existing features browsers provide.
When a page is displayed in Firefox, its url along with its title gets stored in a local
sqlite database, but the whole page content is dropped.

**Places** is adding that full-indexation to unlock search on your browser history.
It uses the latest indexation techniques so you can enable semantic search on your browsing
data. It does not use external APIs for doing it -- to protect your privacy.

For example, you can ask it: "what was the title of the book about training for marathons I read about?"
and it'll find the pages you've browsed before on that topic.

Places use a vector database and indexes content continuously through a web extension (Firefox Only).

There's also a script to index data after the fact, by reading your browsing history (Firefox Only)
or some specific sets of pages via Session Buddy (Chrome)

## Install

You can run Places via its docker image or directly with the source.

### Running locally

```sh
# GPU
make install

# CPU only
make install-cpu
```

### Using Docker

Builds the Places docker image

```sh
# builds the docker image
make build-app-local
```

Note: default install uses GPU, if you don't have one, you can change it to `make install-cpu`

## Run

Start the service locally or via docker:

```sh
# direct, without docker
make run-service

# runs the docker image
make run-docker
```

Then open http://localhost:8080 and install the web extension using the link in the footer.
Once the extension is installed, pages you visit will be indexed.

You can search for content using the URL bar, by typing the `places` prefix,
or go to the service page.
