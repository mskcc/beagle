### Running the Server using Singularity

#### Download Docker Image

```
singularity pull --name mskcc-beagle-1.0.0.img docker://mskcc/beagle:1.0.0
```

##### Starting an instance

```
singularity instance start --bind <beagle_install_directory>:/beagle_server mskcc-beagle-1.0.0.img beagle
```

##### Running the server at port 4001 

```
singularity run instance://beagle python3 /beagle_server/manage.py runserver 0.0.0.0:4001
```

