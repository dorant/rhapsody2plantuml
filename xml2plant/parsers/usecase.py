#!/bin/env python
import logging

from parsers.parser import Participant
from parsers.parser import PartType

from datatypes.usecase import UsecaseDiagramData
from datatypes.usecase import UsecaseData
from datatypes.usecase import UsecaseBox
from datatypes.usecase import UsecaseNote
from datatypes.usecase import UsecaseArrow

# List of all existing usecase diagrams
def get_usecasediagram_list(xml_node):
    result = []
    for usecase in xml_node.findall("ISubsystem/Declaratives/IRPYRawContainer/IUCDiagram"):
        name = usecase.xpath("_name/text()")[0]
        result.append(name)
    return result


def parse_all_usecases(xml_node):

    data_usecases = {}
    for usecase in xml_node.findall("ISubsystem/UseCases/IRPYRawContainer/IUseCase"):
        id = usecase.xpath("_id/text()")[0]
        name = usecase.xpath("_name/text()")[0]
        uc = UsecaseData(id, name)

        statechart_list = usecase.xpath("Diagrams/IRPYRawContainer/IHandle/_id/text()")
        if len(statechart_list) > 0:
            uc.linked_diagram_id = statechart_list[0]

            # Get name of sequence diagram
            seq_list = xml_node.xpath(".//IMSC[_id='" + statechart_list[0] + "']/_name/text()")
            assert len(seq_list) < 2
            if len(seq_list) > 0:
                uc.linked_diagram_name = seq_list[0]

        data_usecases[id] = uc
        logging.debug("Parsed usecase: %s", uc)
    return data_usecases


# Parse a specific diagram
# Return None if failure
def parse_usecasediagram(xml_node, global_participants, find_name):

    # Find the usecase diagram
    diagrams = xml_node.xpath("ISubsystem/Declaratives/IRPYRawContainer/IUCDiagram[_name='" + find_name + "']")
    if len(diagrams) == 0:
        return None

    diagram = diagrams[0]

    name = diagram.xpath("_name/text()")[0]
    diagramdata = UsecaseDiagramData(name)
    logging.debug("Parsing uc-diagram: %s", name)

    # Get all existing usecases
    all_usecases = parse_all_usecases(xml_node)

    # Parse boxes in diagram
    for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIBox"):
        id = cgi.xpath("_id/text()")[0]

        box_name = ""
        box_name_list = cgi.xpath("m_name/CGIText/m_str/text()")
        if len(box_name_list) > 0:
            box_name = box_name_list[0]

        box = UsecaseBox(box_name)
        diagramdata.boxes[id] = box
        logging.debug("  Parsed box: %s", box)

    # Parse usecases in diagram
    for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass"):
        model_id = cgi.xpath("m_pModelObject/IHandle/_id/text()")[0]

        # Handle usecase
        if len(cgi.xpath("m_pModelObject/IHandle[_m2Class='IUseCase']")):
            parent_id = cgi.xpath("m_pParent/text()")[0]
            if not (model_id in all_usecases): return None

            if parent_id in diagramdata.boxes:
                diagramdata.boxes[parent_id].ucs.append(all_usecases[model_id])
                logging.debug("  Adding to box: %s", all_usecases[model_id])
            else:
                diagramdata.ucs.append(all_usecases[model_id])
                logging.debug("  Adding to global: %s", all_usecases[model_id])

        # Handle participants
        elif len(cgi.xpath("m_pModelObject/IHandle[_m2Class='IActor']")):
            if model_id in global_participants:
                diagramdata.participants[model_id] = global_participants[model_id]
            else:
                # Not existing, add a own created
                actor_name = cgi.xpath("m_pModelObject/IHandle/_name/text()")[0]
                diagramdata.participants[model_id] = Participant(PartType.ACTOR, actor_name)
        else:
            return None

    # Parse notes in diagram
    for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIAnnotation"):

        # Get text
        text = ""
        text_list = cgi.xpath("m_name/CGIText/m_str/text()")
        if len(text_list) > 0:
            text = text_list[0]

        note = UsecaseNote(text)

        # Get anchors to note
        id = cgi.xpath("_id/text()")[0]
        for cgi_anchor in diagram.xpath("_graphicChart/CGIClassChart/CGIAnchor[m_pSource='" + id + "']"):
            #logging.debug("Found anchor to note")

            target_list = cgi_anchor.xpath("m_pTarget/text()")
            if len(target_list) != 1: return None

            # Get where its pointing
            for cgi_anchor_object in diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass[_id='" + target_list[0] + "']/m_pModelObject/IHandle/_id/text()"):
                note.anchors.append(cgi_anchor_object)

        for cgi_anchor in diagram.xpath("_graphicChart/CGIClassChart/CGIAnchor[m_pTarget='" + id + "']"):
            #logging.debug("Found anchor to note")

            source_list = cgi_anchor.xpath("m_pSource/text()")
            if len(source_list) != 1: return None

            # Get where its pointing
            for cgi_anchor_object in diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass[_id='" + source_list[0] + "']/m_pModelObject/IHandle/_id/text()"):
                note.anchors.append(cgi_anchor_object)

        logging.debug("  Parsed note: %s", note)
        diagramdata.notes.append(note)


    # Parse associations arrows
    for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIAssociationEnd"):

        #logging.debug("Parsed association id=%s", cgi.xpath("_id/text()"))
        #assert len(cgi.xpath("m_pModelObject/IHandle[_m2Class='IAssociationEnd']")) == 1

        # Get source
        source_node = cgi.xpath("m_pSource/text()")
        if len(source_node) != 1: return None

        # Get where its pointing
        source_list = diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass[_id='" + source_node[0] + "']/m_pModelObject/IHandle/_id/text()")
        if len(source_list) != 1: return None
        source = source_list[0]
    
        # Get target
        target_node = cgi.xpath("m_pTarget/text()")
        if len(target_node) != 1: return None

        # Get where its pointing
        target_list = diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass[_id='" + target_node[0] + "']/m_pModelObject/IHandle/_id/text()")
        if len(target_list) != 1: return None
        target = target_list[0]

        assoc = UsecaseArrow(source, target)
        logging.debug("  Parsed association: %s", assoc)
        diagramdata.associations.append(assoc)

    # Parse inheritance arrows
    for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIInheritance"):
        logging.debug("  Parsed inheritance")

        #assert len(cgi.xpath("m_pModelObject/IHandle[_m2Class='IDependency']")) == 1

        # Get source
        source_node = cgi.xpath("m_pSource/text()")
        if len(source_node) != 1: return None

        # Get where its pointing
        source_list = diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass[_id='" + source_node[0] + "']/m_pModelObject/IHandle/_id/text()")
        if len(source_list) != 1: return None
        source = source_list[0]
    
        # Get target
        target_node = cgi.xpath("m_pTarget/text()")
        if len(target_node) != 1: return None

        # Get where its pointing
        target_list = diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass[_id='" + target_node[0] + "']/m_pModelObject/IHandle/_id/text()")
        if len(target_list) != 1: return None
        target = target_list[0]

        dep = UsecaseArrow(source, target)
        diagramdata.dependencies.append(dep)

    # Done
    return diagramdata
    
