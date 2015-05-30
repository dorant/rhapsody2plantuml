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
First build sbs2xml:
```
cd sbs2xml
mkdir build
cd build
cmake ..
make
```

##### Usage
```
./convert.sh -f ~/my_rhapsody_project

```
