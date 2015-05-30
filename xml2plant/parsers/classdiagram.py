#!/bin/env python
import logging

from parsers.parser import Participant
from parsers.parser import PartType

def get_class_list(xml_node):
    result = []
    for diagram in xml_node.findall("ISubsystem/Declaratives/IRPYRawContainer/IDiagram"):
        name = diagram.xpath("_name/text()")[0]
        result.append(name)
    return result


def parse_classdiagram(xml_node, global_participants, find_name):
    """ Parse a specific class diagram from an xml-node/root 
    """

    diagramdata = {}
    participants = {}

    # Parse a diagram (can exist in a IUseCase as well...
    for diagram in xml_node.findall("ISubsystem/Declaratives/IRPYRawContainer/IDiagram[_name='" + find_name + "']"):

        # Chartname
        diagramdata["name"] = find_name
        logging.debug("Parsing diagram: %s", find_name)

        root = diagram.xpath("_graphicChart/CGIClassChart/m_pRoot/text()")[0]

        # Class
        classes = {}
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIClass"):
            id = cgi.xpath("_id/text()")[0]

            # Parse all classes excpet "TopLevel"
            if id != root:

                if id not in participants:
                    # Check if its pointing to global defined class
                    model_node = cgi.xpath("m_pModelObject/IHandle/_id/text()")
                    if len(model_node) == 1:
                        model_id = model_node[0]
                        if model_id in global_participants:
                            participants[id] = global_participants[model_id]

                if id not in participants:
                    # Check if its pointing to global defined class that not exists in scope
                    model_node = cgi.xpath("m_pModelObject/IHandle/_name/text()")
                    if len(model_node) == 1:
                        name = model_node[0]
                        participants[id] = Participant(PartType.CLASS, name)

                if id not in participants:
                    # Local defined class
                    name_node = cgi.xpath("m_name/CGIText/m_str/text()")
                    if len(name_node) == 1:
                        name = name_node[0]
                        participants[id] = Participant(PartType.CLASS, name)

                if id not in participants:
                    assert None

                logging.debug("Adding class: %s", participants[id].name)
    
                # TODO: remove this duplicate check, should be enough with participants above

                cgiclass = {}

                # Get name
                cgiclass["name"] = participants[id].name

                # Get stereotype
                stereotype_node = cgi.xpath("_properties/IPropertyContainer/Subjects/IRPYRawContainer/IPropertySubject[_Name='ObjectModelGe']/Metaclasses/IRPYRawContainer/IPropertyMetaclass/_Name/text()")
                if len(stereotype_node) > 0:
                    cgiclass["stereotype"] = stereotype_node[0]

                # Get parent
                parent_node = cgi.xpath("m_pParent/text()")
                assert len(parent_node) == 1
                cgiclass["parent"] = parent_node[0]

                classes[id] = cgiclass
                #print id, "Class:", cgiclass

        diagramdata["classes"] = classes

        # Types
        types = {}
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIGenericElement"):
            id = cgi.xpath("_id/text()")[0]

            if len(cgi.xpath("m_pModelObject/IHandle[_m2Class='IType']")):

                name_list = cgi.xpath("m_name/CGIText/m_str/text()")
                if len(name_list) > 0:

                    cgitype = {}

                    # Get name
                    cgitype["name"] = name_list[0]

                    # Get parent
                    parent_node = cgi.xpath("m_pParent/text()")
                    assert len(parent_node) == 1
                    cgitype["parent"] = parent_node[0]

                    types[id] = cgitype
                    logging.debug("Adding type: %s", cgiclass["name"])
        diagramdata["types"] = types

        # Modules/Files
        modules = {}
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIObjectInstance"):
            id = cgi.xpath("_id/text()")[0]

            if len(cgi.xpath("m_pModelObject/IHandle[_m2Class='IModule']")):

                name_list = cgi.xpath("m_name/CGIText/m_str/text()")
                if len(name_list) > 0:

                    cgimodule = {}
                
                    # Get name
                    cgimodule["name"] = name_list[0]

                    # Get parent
                    parent_node = cgi.xpath("m_pParent/text()")
                    assert len(parent_node) == 1
                    cgimodule["parent"] = parent_node[0]

                    modules[id] = cgimodule
                    logging.debug("Adding type: %s", cgiclass["name"])
        diagramdata["modules"] = modules

        # Actor (which is possible..)
        actors = {}
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass"):
            id = cgi.xpath("_id/text()")[0]

            if len(cgi.xpath("m_pModelObject/IHandle[_m2Class='IActor']")):

                name_list = cgi.xpath("m_name/CGIText/m_str/text()")
                if len(name_list) > 0:
                    actors[id] = name_list[0]
                    logging.debug("Adding actor: %s", actors[id])

        diagramdata["actors"] = actors

        # Associations
        associations = []
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIAssociationEnd"):
            # Source
            source_node = cgi.xpath("m_pSource/text()")
            assert len(source_node) == 1
            source = source_node[0]

            sourcerole = ""
            sourcerole_node = cgi.xpath("m_sourceRole/CGIText/m_str/text()")
            if len(sourcerole_node) > 0:
                sourcerole = sourcerole_node[0]

            sourcemulti = ""
            sourcemulti_node = cgi.xpath("m_sourceMultiplicity/CGIText/m_str/text()")
            if len(sourcemulti_node) > 0:
                sourcemulti = sourcemulti_node[0]

            # Target
            target_node = cgi.xpath("m_pTarget/text()")
            assert len(target_node) == 1
            target = target_node[0]

            targetrole = ""
            targetrole_node = cgi.xpath("m_targetRole/CGIText/m_str/text()")
            if len(targetrole_node) > 0:
                targetrole = targetrole_node[0]

            targetmulti = ""
            targetmulti_node = cgi.xpath("m_targetMultiplicity/CGIText/m_str/text()")
            if len(targetmulti_node) > 0:
                targetmulti = targetmulti_node[0]

            assoc = {}
            assoc["source"] = classes[source]["name"]
            assoc["sourcerole"] = sourcerole
            assoc["sourcemultiplicity"] = sourcemulti
            assoc["target"] = classes[target]["name"]
            assoc["targetrole"] = targetrole
            assoc["targetmultiplicity"] = targetmulti
            associations.append(assoc)
            logging.debug("Adding association: %s - %s", assoc["source"], assoc["target"])

        diagramdata["associations"] = associations

        # Packages
        packages = {}
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIPackage"):
            pkg_node = cgi.xpath("m_name/CGIText/m_str/text()")
            if len(pkg_node) > 0:
                name = pkg_node[0]
                id_node = cgi.xpath("_id/text()")
                assert len(id_node) == 1
                id = id_node[0]

                pkg = {}
                pkg["name"] = name
                pkg["includes"] = []
                for classid in classes:
                    if classes[classid]["parent"] == id:
                        pkg["includes"].append(classes[classid]["name"])

                packages[id] = pkg
                logging.debug("Adding package: %s", name)

        diagramdata["packages"] = packages

        # Inheritance
        inheritance = []
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIInheritance"):
            source_node = cgi.xpath("m_pSource/text()")
            assert len(source_node) == 1
            source = source_node[0]

            target_node = cgi.xpath("m_pTarget/text()")
            assert len(target_node) == 1
            target = target_node[0]
            logging.debug("Got source=%s target=%s", source, target)

            inherit = {}
            if source in classes:
                inherit["source"] = classes[source]["name"]
            if source in packages:
                inherit["source"] = packages[source]["name"]
            if source in actors:
                inherit["source"] = actors[source]
            if source in types:
                inherit["source"] = types[source]["name"]
            if source in modules:
                inherit["source"] = modules[source]["name"]
            assert inherit["source"]

            if target in classes:
                inherit["target"] = classes[target]["name"]
            if target in packages:
                inherit["target"] = packages[target]["name"]
            if target in actors:
                inherit["target"] = actors[target]
            if target in types:
                inherit["target"] = types[target]["name"]
            if target in modules:
                inherit["target"] = modules[target]["name"]
            assert inherit["target"]

            inheritance.append(inherit)
            logging.debug("Adding inheritance: %s - %s", inherit["source"], inherit["target"])

        diagramdata["inheritance"] = inheritance

    # Done
    assert "name" in diagramdata
    return diagramdata
