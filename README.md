- [Places](#places)
- [Install](#install)
  - [Local](#local)
  - [Docker](#docker)
- [Run](#run)
- [Indexing](#indexing)
- [View](#view)


**Experimental**


[![Tests](https://github.com/myinternets/places/actions/workflows/test.yml/badge.svg?event=push)](https://github.com/myinternets/places/actions/workflows/ruff.yml)

[![Docker Image CI](https://github.com/myinternets/places/actions/workflows/docker-image.yml/badge.svg)](https://github.com/myinternets/places/actions/workflows/docker-image.yml)


Places
------

*Semantic Search on your Browser History.*


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
make build-app
```

Note: default install uses GPU, if you don't have one, you can change it to `make install-cpu`


### Installing the web extension (Firefox)

Use a pre-release [open me in Firefox](https://github.com/myinternets/places/releases/download/v0.0.4/places@ziade.org.xpi)

Alternatively, you can install a temporary extension. Open `about:debugging` in
your browser and load a temporary extension in "This Firefox" -- you can browse
into the `firefox` dir in the project and select any file. Once it's installed
you can clik on the toolbar on the `extensions` icon and add the magnifier to
your toolbar. It's a link to `http://localhost:8080` to display the search
page.


## Run

If you use the Qdrant backend, run Qdrant first with:

```sh
make run-quadrant
```

And then the service:

```sh
# direct, without docker
make web

# runs the docker image
make run-app
```

If you want to run using the built-in Vectra backend (no extra service required) you can
just run the web service with

```sh
make run-standalone-web
```


## Indexing

If you added the extension, the indexation will occur as you surf the web.

You can also index old content in Firefox data by using the `index.py` script and 
your profile's `places.sqlite` file.

It is recommended to use a copy to avoid locking issues.

Indexing data from that file will visit url it finds there and it will
take a lot of time. It will also fail to index pages that require authentication
and might also temporarely ban you from some domains. For instance if you are an avid
Stack Overflow user, scraping their website will get you temporarely banned and
you won't get all the content you've once browsed.

This indexation feature is just useful to experiment on more content with a one
time indexation, it's not really meant to be used all the time.


```sh
# from virtualenv (source .venv/bin/activate)
places index /path/to/places.sqlite

# or (if places.sqlite is in the current directory)
make index 
```

## View

Then open (even while it's indexing)  http://localhost:8080
