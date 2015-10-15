## Convert IBM Rhapsody diagrams to PlantUML

With this tool you can convert your:
* Usecase diagrams
* Sequence diagrams
* Class/Object diagrams

to [PlantUML](http://plantuml.sourceforge.net) syntax


##### Tools
* convert.sh - script to convert all .sbs'es in given path, uses below tools
* sbs2xml    - tool to convert .sbs to XML format
* xml2plant  - tool to convert above XML to PlantUML syntax

##### Setup
First build the needed tools (sbs2xml) and install it:
```
cd <repo>
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=<path to install to> ../
make install
```

##### Usage
Convert all existing diagrams in a project.
The command will stop when hitting an error.
```
./convert.sh ~/my_rhapsody_project
```

Using the force flag all diagrams can be converted even if a single diagram fails:
```
./convert.sh -f ~/my_rhapsody_project
```

Verify the result using the PlantUML syntax checker
```
./convert.sh -c plantuml.8030.jar -f ~/my_rhapsody_project
```
