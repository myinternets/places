places
------

**Experimental**

Semantic Search on your Browser History

To run, build the docker image containing Qdrant and the app, then run it

```
make install build-app run-app
```

Then index the Firefox data using the `index.py` script and the path
to the profile's `places.sqlite` file.

```
places index /path/to/places.sqlite
```

Then open (even while it's indexing)  http://localhost:8080
