#!/bin/env python
import sys
import logging
from lxml import etree
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter


def enum(*args):
    enums = dict(zip(args, range(len(args))))
    return type('Enum', (), enums)

# Handle: m_transform
# m_transform = <width> 0 0 <height> <TL Absolute X> <TL Absolute Y.yyyy>
class Transform:
    def __init__(self, string=None):
        if string:
            strlist = string.split()        
            self.scale_width  = float(strlist[0])
            self.scale_height = float(strlist[3])
            self.x = float(strlist[4])
            self.y = float(strlist[5])
        else:
            self.scale_width = 1
            self.scale_height = 1
            self.x = 0
            self.y = 0

    def __str__(self):
        return "Transform(w=%s, h=%s, x=%s, y=%s)" % (self.scale_width,
                                                      self.scale_height,
                                                      self.x, 
                                                      self.y)

class Position:
    def __init__(self, string=None):        
       if string != None:
           strlist = string.split()
           self.top_left_x = float(strlist[1])
           self.top_left_y = float(strlist[2])
           self.bottom_left_x = float(strlist[3])
           self.bottom_left_y = float(strlist[4])
           self.bottom_right_x = float(strlist[5])
           self.bottom_right_y = float(strlist[6])
           self.top_right_x = float(strlist[7])
           self.top_right_y = float(strlist[8])
       else:
           self.top_left_x = 0
           self.top_left_y = 0
           self.top_right_x = 0
           self.top_right_y = 0
           self.bottom_left_x = 0
           self.bottom_left_y = 0
           self.bottom_right_x = 0
           self.bottom_right_y = 0

    def make_int(self):
        self.top_left_x = int(self.top_left_x)
        self.top_left_y = int(self.top_left_y)
        self.top_right_x = int(self.top_right_x)
        self.top_right_y = int(self.top_right_y)
        self.bottom_left_x = int(self.bottom_left_x)
        self.bottom_left_y = int(self.bottom_left_y)
        self.bottom_right_x = int(self.bottom_right_x)
        self.bottom_right_y = int(self.bottom_right_y)

    def parsePolygon(self, string):
        ''' The polygon can be any order for each (x y) '''
        strlist = string.split()
        num = strlist.pop(0)
        assert num == "4"

        xlist = [float(strlist[0]),
                 float(strlist[2]),
                 float(strlist[4]),
                 float(strlist[6])]

        ylist = [float(strlist[1]),
                 float(strlist[3]),
                 float(strlist[5]),
                 float(strlist[7])]

        # We only support rectangles, only 2 unique values in coordinate each
        assert len(set(xlist)) == 2
        assert len(set(ylist)) == 2

        self.top_left_x = min(xlist)
        self.top_left_y = min(ylist)
        self.bottom_left_x = min(xlist)
        self.bottom_left_y = max(ylist)
        self.bottom_right_x = max(xlist)
        self.bottom_right_y = max(ylist)
        self.top_right_x = max(xlist)
        self.top_right_y = min(ylist)

# TODO: remove
    def transform(self, trans):

        # Calculate new width
        new_top_width = int((self.top_right_x - self.top_left_x) * trans.scale_width)
        new_bottom_width = int((self.bottom_right_x - self.bottom_left_x) * trans.scale_width)

        # Calculate new height
        new_left_height = int((self.bottom_left_y - self.top_left_y) * trans.scale_height)
        new_right_height= int((self.bottom_right_y - self.top_right_y) * trans.scale_height)

        # Add movement
        self.top_left_x    += float(trans.x)
        self.top_left_y    += float(trans.y)
        self.bottom_left_x += float(trans.x)
        self.top_right_y   += float(trans.y)

        # Set new height
        self.bottom_left_y = self.top_left_y + new_left_height
        self.bottom_right_y = self.top_right_y + new_right_height

        # Set new width
        self.top_right_x = self.top_left_x + new_top_width
        self.bottom_right_x = self.bottom_left_x + new_bottom_width


    def get_center_x(self):        
           return (self.top_right_x - self.top_left_x)/2 + self.top_left_x

    def get_center_y(self):        
           return (self.bottom_left_y - self.top_left_y)/2 + self.top_left_y

    def get_width(self):        
           return self.top_right_x - self.top_left_x 

    def get_height(self):        
           return self.bottom_left_y - self.top_left_y 

    def __str__(self):
        return "Position(TL:%s %s, TR:%s %s, BL:%s %s, BR:%s %s)" % (self.top_left_x, self.top_left_y,
                                                                     self.top_right_x, self.top_right_y,
                                                                     self.bottom_left_x, self.bottom_left_y,
                                                                     self.bottom_right_x, self.bottom_right_y)


PartType = enum('CLASS', 'INTERFACE', 'ACTOR')

class Participant:
    def __init__(self, type, name=""):
        if type not in (PartType.CLASS, PartType.INTERFACE, PartType.ACTOR):
            raise ValueError('type not valid')
        self.type = type
        self.name = name
        self.fillstyle = 0
        self.position = Position()
        self.associations = []
        self.dependencies = []

    def type_to_string(self):
        if self.type == PartType.CLASS:
            return "Class"
        elif self.type == PartType.INTERFACE:
            return "Interface"
        elif self.type == PartType.ACTOR:
            return "Actor"
        else:
            assert None

    def __str__(self):
        return "Participant(%s %s %s %s %s)" % (self.type_to_string(), self.name, 
                                                self.dependencies, self.associations,
                                                self.position)


EventType = enum('MESSAGE', 'COND_START', 'COND_ELSE', 'COND_END', 'NOTE', 'DIVIDER', 'REF')

class Event(object):
    def __init__(self, type):
        if type not in (EventType.MESSAGE, EventType.COND_START, EventType.COND_ELSE,
                        EventType.COND_END, EventType.NOTE, EventType.DIVIDER, EventType.REF):
            raise ValueError('type not valid')
        self.type = type
        self.id = ""
        self.position = Position()

    def __str__(self):
        return "Event(%s %s %s)" % (self.type, self.id, self.position)


MessageType = enum('PRIMITIVE', 'REPLY')
class Message(Event):
    def __init__(self):
        super(Message, self).__init__(EventType.MESSAGE)
        self.name = ""
        self.args = ""
        self.seq = 0
        self.sender = ""
        self.receiver = ""
        self.msgtype = MessageType.PRIMITIVE
        self.source = ""
        self.target = ""
        
    def __str__(self):
        return "Message(%s)" % (self.name)

class ConditionStart(Event):
    def __init__(self):
        super(ConditionStart, self).__init__(EventType.COND_START)
        self.cond = ""
        self.text = ""

    def __str__(self):
        return "ConditionStart(%s %s)" % (self.cond, self.position)

class ConditionElse(Event):
    def __init__(self):
        super(ConditionElse, self).__init__(EventType.COND_ELSE)
        self.cond = "else"
        self.text = ""

    def __str__(self):
        return "ConditionElse(%s %s)" % (self.cond, self.position)


class ConditionEnd(Event):
    def __init__(self):
        super(ConditionEnd, self).__init__(EventType.COND_END)
    def __str__(self):
        return "ConditionEnd(%s)" % (self.position)

class Note(Event):
    def __init__(self):
        super(Note, self).__init__(EventType.NOTE)
        self.text = ""
    def __str__(self):
        return "Note(%s)" % (self.position)

class Divider(Event):
    def __init__(self):
        super(Divider, self).__init__(EventType.DIVIDER)
        self.text = ""
    def __str__(self):
        return "Divider(%s)" % (self.position)

class Reference(Event):
    def __init__(self):
        super(Reference, self).__init__(EventType.REF)
        self.text = ""
    def __str__(self):
        return "Reference(%s)" % (self.position)

        
# GLOBALS
global_participants = {}

# Global level
def parse_classes(xml_node):
    """ Get all classes from an xml-node/root
    """
    global global_participants
    for iclass in xml_node.findall("ISubsystem/Classes/IRPYRawContainer/IClass"):
        # Only add real classes
        if int(iclass.xpath("_myState/text()")[0]) == 8192:
            name = iclass.xpath("_name/text()")[0]
            id = iclass.xpath("_id/text()")[0]

            type = PartType.CLASS
            for stereotype in iclass.xpath("Stereotypes/IRPYRawContainer/IHandle/_name/text()"):
                if stereotype == "Interface":
                    type = PartType.INTERFACE

            global_participants[id] = Participant(type, name)
            logging.debug("Added: %s for id=%s", global_participants[id], id)
    logging.debug("Added %s classes/interfaces", len(global_participants))


# Global level
def parse_actors(xml_node):
    """ Get all actors from an xml-node/root
    """
    global global_participants
    for iactor in xml_node.findall(".//ISubsystem/Actors/IRPYRawContainer/IActor"):
        if int(iactor.xpath("_myState/text()")[0]) == 8192:
            name = iactor.xpath("_name/text()")[0]
            id = iactor.xpath("_id/text()")[0]

            actor = Participant(PartType.ACTOR, name)

            for depend_node in iactor.xpath("Dependencies/IRPYRawContainer/IDependency"):
                dependType = depend_node.xpath("_dependsOn/INObjectHandle/_m2Class/text()")[0]
                if dependType == "IActor" or dependType == "IUseCase":
                    actor.dependencies.append(depend_node.xpath("_dependsOn/INObjectHandle/_id/text()")[0])

            for assoc_node in iactor.xpath("Associations/IRPYRawContainer/IAssociationEnd"):
                if assoc_node.xpath("_otherClass/IClassifierHandle/_m2Class/text()")[0] == "IUseCase":
                    actor.associations.append(assoc_node.xpath("_otherClass/IClassifierHandle/_id/text()")[0])

            global_participants[id] = actor
            logging.debug("Added: %s", global_participants[id])

# Parse a opt-box in a statechart
def parse_conditions(node, events_result):
    for occur in node.xpath("InteractionOccurrences/IRPYRawContainer/IInteractionOccurrence"):
        msg = Reference()
        msg.id = occur.xpath("_id/text()")[0]
        msg.text = occur.xpath("_name/text()")[0]
        events_result.append(msg)

    for fragment in node.xpath("CombinedFragments/IRPYRawContainer/ICombinedFragment"):
        cond = fragment.xpath("_interactionOperator/text()")[0]
        last_id = None
        for operand in fragment.xpath("InteractionOperands/IRPYRawContainer/IInteractionOperand"):
            id = operand.xpath("_id/text()")[0]

            # Start
            if not last_id:
                msg = ConditionStart()
                msg.cond = cond
                msg.text = operand.xpath("_interactionConstraint/text()")[0]
                msg.id = id
                logging.debug("Added start: %s", msg)
                logging.debug("         id: %s", id)
                logging.debug("       type: %s", cond)


            else:
                msg = ConditionElse()
                msg.text = operand.xpath("_interactionConstraint/text()")[0]
                msg.id = id
                logging.debug("Added  else: %s", msg)
                logging.debug("         id: %s", id)
                logging.debug("       type: %s", "else")

            last_id = id
            events_result.append(msg)

            parse_conditions(operand, events_result)

        # End
        msg = ConditionEnd()
        msg.id = last_id
        events_result.append(msg)

        logging.debug("Added   end: %s", msg)
        logging.debug("         id: %s", last_id)
        logging.debug("       type: %s", cond)


def parse_usecases(xml_node, find_name):

    data_usecases = {}
    for usecase in xml_node.findall(".//ISubsystem/UseCases/IRPYRawContainer/IUseCase"):
        name = usecase.xpath("_name/text()")[0]
        id = usecase.xpath("_id/text()")[0]

        statechart = ""
        statechart_list = usecase.xpath("Diagrams/IRPYRawContainer/IHandle/_id/text()")
        if len(statechart_list) > 0:
            statechart = statechart_list[0]

        depend = []
        for depend_node in usecase.xpath("Dependencies/IRPYRawContainer/IDependency"):
            if depend_node.xpath("_dependsOn/INObjectHandle/_m2Class/text()")[0] == "IUseCase":
                depend.append(depend_node.xpath("_dependsOn/INObjectHandle/_id/text()")[0])

        associations = []
        for assoc_node in usecase.xpath("Associations/IRPYRawContainer/IAssociationEnd"):
            if assoc_node.xpath("_otherClass/IClassifierHandle/_m2Class/text()")[0] == "IActor":
                associations.append(assoc_node.xpath("_otherClass/IClassifierHandle/_id/text()")[0])

        data_usecase = {}
        data_usecase['name'] = name
        data_usecase['dependencies'] = depend
        data_usecase['associations'] = associations
        data_usecase['statechart'] = statechart
        data_usecases[id] = data_usecase
        logging.debug("Parsed usecase: %s", data_usecase)

    data_diagrams = {}
    for diagram in xml_node.xpath(".//ISubsystem/Declaratives/IRPYRawContainer/IUCDiagram[_name='" + find_name + "']"):
        name = diagram.xpath("_name/text()")[0]
        logging.debug("Parsed uc-diagram name: %s", name)

        # Parse boxes in diagram
        data_diagram_rects = {}
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIBox"):
            id = cgi.xpath("_id/text()")[0]

            box_name = ""
            box_name_list = cgi.xpath("m_name/CGIText/m_str/text()")
            if len(box_name_list) > 0:
                box_name = box_name_list[0]

            data_diagram_rect = {}
            data_diagram_rect['name'] = box_name
            data_diagram_rect['ucs']  = []
            data_diagram_rects[id] = data_diagram_rect

        # Parse usecases in diagram
        data_diagram_ucs = []
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass"):
            parent = cgi.xpath("m_pParent/text()")[0]
            guids = cgi.xpath("m_pModelObject/IHandle/_id/text()")
            if len(guids) > 0 and guids[0] in data_usecases:
                id = guids[0]
                if parent in data_diagram_rects:
                    data_diagram_rects[parent]['ucs'].append(id)
                else:
                    data_diagram_ucs.append(id)

        logging.debug("Parsed free usecases: %s", data_diagram_ucs)
        logging.debug("Parsed uc-diagram boxes: %s", data_diagram_rects)
                    
        # Add results
        data_diagram = {}
        data_diagram["rect_ucs"] = data_diagram_rects
        data_diagram["free_ucs"] = data_diagram_ucs
        data_diagrams[name] = data_diagram

    return data_usecases, data_diagrams



def get_scale_factor(type, cgi_node, guid):
    root_guid = cgi_node.xpath("m_pRoot/text()")[0]

    cgi_items = cgi_node.xpath("*[_id='"+guid+"']")
    assert len(cgi_items) == 1

    # Get factor/transform info for current item
    transform = Transform()
    transform_node = cgi_items[0].xpath("m_transform/text()")
    if len(transform_node) > 0:
        assert len(transform_node) == 1
        transform = Transform(transform_node[0])

    parent_node = cgi_items[0].xpath("m_pParent/text()")
    assert len(parent_node) == 1

    base_factor = 1
    if parent_node[0] != root_guid:
        base_factor = get_scale_factor(type, cgi_node, parent_node[0])
        
    if type == "height":
        return transform.scale_height * base_factor
    else:
        return transform.scale_width * base_factor


def calculate_base_scale(type, cgi_node, guid, value):

    cgi_items = cgi_node.xpath("*[_id='"+guid+"']")
    assert len(cgi_items) == 1

    # Dont calculate if we got the root as base
    root_guid = cgi_node.xpath("m_pRoot/text()")[0]
    if guid == root_guid:
        return value

    position = Position()
    polygon_node = cgi_items[0].xpath("m_polygon/text()")
    assert len(polygon_node) == 1
    position.parsePolygon(polygon_node[0])

    # Get factor/transform info for current item
    transform = Transform()
    transform_node = cgi_items[0].xpath("m_transform/text()")
    if len(transform_node) > 0:
        assert len(transform_node) == 1
        transform = Transform(transform_node[0])

    # Calculate scaled value
    if type == "x":
        result = (value * transform.scale_width) + transform.x
    else:
        result = (value * transform.scale_height) + transform.y

    parent_node = cgi_items[0].xpath("m_pParent/text()")
    assert len(parent_node) == 1
    if parent_node[0] != root_guid:
        return calculate_base_scale(type, cgi_node, parent_node[0], result)
    else:
        return result


def get_merged_position(cgi_node, guid):

    cgi_items = cgi_node.xpath("*[_id='"+guid+"']")
    assert len(cgi_items) == 1

    polygon_node = cgi_items[0].xpath("m_polygon/text()")
    assert len(polygon_node) == 1
    position = Position()
    position.parsePolygon(polygon_node[0])
    logging.debug("Merge: %s", position)

    transform = Transform()
    transform_node = cgi_items[0].xpath("m_transform/text()")
    if len(transform_node) > 0:
        assert len(transform_node) == 1
        transform = Transform(transform_node[0])
        logging.debug("Merge: %s", transform)

    root_guid = cgi_node.xpath("m_pRoot/text()")[0]
    parent_node = cgi_items[0].xpath("m_pParent/text()")
    assert len(parent_node) == 1

    if parent_node[0] != root_guid:
        logging.debug("Merge: Base is non-root: %s", parent_node[0])
    else:
        logging.debug("Merge: Base is root")

    scaled_height = position.get_height() * get_scale_factor("height", cgi_node, guid)
    scaled_width  = position.get_width()  * get_scale_factor("width", cgi_node, guid)

    calc_x = (position.top_left_x + transform.x)
    calc_y = (position.top_left_y + transform.y)

    result = Position()
    result.top_left_x = calculate_base_scale("x", cgi_node, parent_node[0], calc_x)
    result.top_left_y = calculate_base_scale("y", cgi_node, parent_node[0], calc_y)
    result.top_right_x = result.top_left_x + scaled_width
    result.top_right_y = result.top_left_y
    result.bottom_left_x = result.top_left_x
    result.bottom_left_y = result.top_left_y + scaled_height
    result.bottom_right_x = result.top_right_x
    result.bottom_right_y = result.bottom_left_y
    result.make_int()
    return result


def parse_sequencediagram(xml_node, find_name):
    """ Parse a specific sequence diagram from an xml-node/root 
    """
    global global_participants
    global data_lifelines
    chartdata = {}

    # Parse a diagram (can exist in a IUseCase as well...
    for chart in xml_node.xpath(".//IMSC[_name='" + find_name + "']"):


        # Chartname
        chartdata["name"] = chart.xpath("_name/text()")[0]

        # Get nodes
        collaboration = chart.xpath("m_pICollaboration/ICollaboration")[0]

        # Lifelines
        data_lifelines = {}
        for iroles in collaboration.xpath("ClassifierRoles/IRPYRawContainer/IClassifierRole"):

            type = PartType.CLASS
            if iroles.xpath("m_eRoleType/text()")[0] == "IActor":
                type = PartType.ACTOR

            part = Participant(type)

            names = iroles.xpath("_name/text()")
            if len(names) > 0:
                part.name = names[0]
            else:
                handle_name = iroles.xpath("m_pBase/IHandle/_name/text()")
                if len(handle_name) > 0:
                    part.name  = handle_name[0]
                else:
                    guid = iroles.xpath("m_pBase/IHandle/_id/text()")[0]
                    if guid in global_participants:
                        part.name = global_participants[guid].name
                    else:
                        part.name = "Unknown"
                    
            id = iroles.xpath("_id/text()")[0]
            data_lifelines[id] = part


        # Messages
        chartdata["events"] = []
        for imessage in collaboration.xpath("Messages/IRPYRawContainer/IMessage"):
            msg = Message()
            msg.name = imessage.xpath("_name/text()")[0]

            args = imessage.xpath("m_szActualArgs/text()")
            if len(args) > 0:
                msg.args = args[0]

            seq_node = imessage.xpath("m_szSequence/text()")
            if len(seq_node) > 0:
                msg.seq = int(seq_node[0].split(".")[0])
            msg.sender = imessage.xpath("m_pSender/IHandle/_id/text()")[0]
            msg.receiver = imessage.xpath("m_pReceiver/IHandle/_id/text()")[0]
            msg.id = imessage.xpath("_id/text()")[0]

            # Arrow style (PRIMITIVE (Default)/ REPLY)
            if imessage.xpath("m_eType/text()")[0] == "REPLY":
                msg.msgtype = MessageType.REPLY

            chartdata["events"].append(msg)
            logging.debug("Added: %s", msg)


        # Conditions (loop, opt..) (CombinedFragments)
        parse_conditions(collaboration, chartdata["events"])

        # -- Now start parsing graphics info (CGI) ---
        cgi = chart.xpath("_graphicChart/CGIMscChart")[0]
        
        # This is the statechart global conversion factor port->y
        msg_port_factor = None

        # CGI: Colums/splitlines - add extra info
        for column in cgi.xpath("CGIMscColumnCR"):
            guids = column.xpath("m_pModelObject/IHandle/_id/text()")
            if len(guids) > 0 and guids[0] in data_lifelines:
                id = guids[0]

                data_lifelines[id].position = Position(column.xpath("m_position/text()")[0])

                transform_node = column.xpath("m_transform/text()")
                assert len(transform_node) == 1
                transform = Transform(transform_node[0])
#TODO: remove transform
                data_lifelines[id].position.transform(transform)
                logging.debug("Transform %s", transform)
                logging.debug("Updated %s", data_lifelines[id])

                if not msg_port_factor:
                    msg_port_factor = transform.scale_height

                path = "_properties/IPropertyContainer/Subjects/IRPYRawContainer/IPropertySubject/Metaclasses/IRPYRawContainer/IPropertyMetaclass/Properties/IRPYRawContainer/"
                property_fill = column.xpath(path + "IProperty[_Name='Fill.FillStyle']/_Value/text()")
                if len(property_fill) > 0:
                    data_lifelines[id].fillstyle = int(property_fill[0])
                else:
                    property_color = column.xpath(path + "IProperty[_Name='Fill.FillColor']/_Value/text()")
                    if len(property_color) > 0:
                        data_lifelines[id].fillstyle = property_color[0]
            else:
                # Check for splitlines/dividers
                if int(column.xpath("m_type/text()")[0]) == 120:
                    msg = Divider()
                    msg.text = column.xpath("m_name/CGIText/m_str/text()")[0]

                    msg.position = Position()
                    transform = Transform(column.xpath("m_transform/text()")[0])
# TODO: remove transform!
                    msg.position.transform(transform)
                    
                    chartdata["events"].append(msg)
                    logging.debug("Added: %s", msg)

        # CGI: Messages - add extra info 
        for message in cgi.xpath("CGIMscMessage"):
            guids = message.xpath("m_pModelObject/IHandle/_id/text()")
            if len(guids) > 0:
                id = guids[0]
                for event in chartdata["events"]:
                    if event.id == id:
                        event.source = message.xpath("m_pSource/text()")
                        event.target = message.xpath("m_pTarget/text()")

                        # Calculate y using factor given by lifeline-data
                        # The value is not including the top 50 pixels
                        assert msg_port_factor != None
                        port = message.xpath("m_SourcePort/text()")[0]
                        assert int(port.split()[0]) == 48
                        port = int(port.split()[1])
                        y_value = int(port * msg_port_factor) + 50

                        event.position.top_left_y = y_value
                        event.position.bottom_left_y = y_value
                        event.position.top_right_y = y_value
                        event.position.bottom_right_y = y_value

                        logging.debug("Updated: %s Port: %s", event, port)

        # CGI: References
        for operand in cgi.xpath("CGIMscInteractionOccurrence"):
            id_node = operand.xpath("_id/text()")
            assert len(id_node) == 1
            id = id_node[0]

            model_node = operand.xpath("m_pModelObject/IHandle/_id/text()")
            assert len(model_node) == 1
            model_id = model_node[0]

            for event in chartdata["events"]:
                if event.id == model_id:
                    # Parse and add the text of the note
                    text_node = operand.xpath("m_name/CGIText/m_str/text()")
                    if len(text_node) > 0:
                        event.text = text_node[0]

                    # Get position
                    event.position = get_merged_position(cgi, id)

                    logging.debug("Updated: %s", event)


        # CGI: Operand (loop, opt..)
        for operand in cgi.xpath("CGIMscInteractionOperator"):
            id_node = operand.xpath("_id/text()")
            assert len(id_node) == 1
            id = id_node[0]

            model_node = operand.xpath("m_pModelObject/IHandle/_id/text()")
            assert len(model_node) == 1
            model_id = model_node[0]

            for event in chartdata["events"]:
                if event.id == model_id:

                    position = get_merged_position(cgi, id)

                    if event.type == EventType.COND_START or event.type == EventType.COND_ELSE:
                        event.position = position

                        logging.debug("Operator-Updated: %s", event)

                    elif event.type == EventType.COND_END:
                        new_pos = Position()
                        new_pos.top_left_x = position.bottom_left_x
                        new_pos.top_left_y = position.bottom_left_y
                        new_pos.bottom_left_x = position.bottom_left_x
                        new_pos.bottom_left_y = position.bottom_left_y
                        new_pos.top_right_x = position.bottom_right_x
                        new_pos.top_right_y = position.bottom_right_y
                        new_pos.bottom_right_x = position.bottom_right_x
                        new_pos.bottom_right_y = position.bottom_right_y
                        event.position = new_pos
                        logging.debug("Operator-Updated: %s", event)

        for operand in cgi.xpath("CGIMscInteractionOperand"):
            id_node = operand.xpath("_id/text()")
            assert len(id_node) == 1
            id = id_node[0]

            model_node = operand.xpath("m_pModelObject/IHandle/_id/text()")
            assert len(model_node) == 1
            model_id = model_node[0]

            for event in chartdata["events"]:
                if event.id == model_id:

                    position = get_merged_position(cgi, id)

                    if event.type == EventType.COND_START:
                        event.position = position
                        logging.debug("Updated: %s", event)
                    elif event.type == EventType.COND_ELSE:
                        event.position = position
                        logging.debug("Updated: %s", event)
                    elif event.type == EventType.COND_END:
                        new_pos = Position()
                        new_pos.top_left_x = position.bottom_left_x
                        new_pos.top_left_y = position.bottom_left_y
                        new_pos.bottom_left_x = position.bottom_left_x
                        new_pos.bottom_left_y = position.bottom_left_y
                        new_pos.top_right_x = position.bottom_right_x
                        new_pos.top_right_y = position.bottom_right_y
                        new_pos.bottom_right_x = position.bottom_right_x
                        new_pos.bottom_right_y = position.bottom_right_y
                        event.position = new_pos
                        logging.debug("Updated: %s", event)


        # Notes
        for note in cgi.xpath("CGIAnnotation"):
            msg = Note()
            guids = note.xpath("_id/text()")
            assert len(guids) == 1
            id = guids[0]

            # Parse and add the text of the note
            text_node = note.xpath("m_name/CGIText/m_str/text()")
            if len(text_node) > 0:
                msg.text = text_node[0]

            # Get note position
            msg.position = get_merged_position(cgi, id)

            chartdata["events"].append(msg)
            logging.debug("Added: %s", msg)


        # Anchor
        # Can point to: CGIAnnotation(Note), CGIMscMessage
# TODO: handle this
        data_anchor = {}
        for anchor in chart.xpath("_graphicChart/CGIMscChart/CGIAnchor"):
            pass
            #print anchor.xpath("m_pSource/text()")[0]
            #print anchor.xpath("m_pTarget/text()")[0]

    # Done
    return chartdata


def parse_classdiagram(xml_node, find_name):
    """ Parse a specific class diagram from an xml-node/root 
    """
    global global_participants
    diagramdata = {}

    # Parse a diagram (can exist in a IUseCase as well...
    for diagram in xml_node.findall(".//ISubsystem/Declaratives/IRPYRawContainer/IDiagram[_name='" + find_name + "']"):
        name = diagram.xpath("_name/text()")[0]
        print "  ", name

        # Chartname
        diagramdata["name"] = diagram.xpath("_name/text()")[0]

        root = diagram.xpath("_graphicChart/CGIClassChart/m_pRoot/text()")[0]

        # Class
        classes = {}
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIClass"):
            id_node = cgi.xpath("_id/text()")
            assert len(id_node) == 1
            id = id_node[0]

            if id != root:
                cgiclass = {}
                # Get name
                model_node = cgi.xpath("m_pModelObject/IHandle/_name/text()")
                if len(model_node) == 1:
                    name = model_node[0]
                else:
                    model_node = cgi.xpath("m_pModelObject/IHandle/_id/text()")
                    assert len(model_node) == 1
                    model_id = model_node[0]
                    name = global_participants[model_id].name

                cgiclass["name"] = name

                # Get stereotype
                stereotype_node = cgi.xpath("_properties/IPropertyContainer/Subjects/IRPYRawContainer/IPropertySubject[_Name='ObjectModelGe']/Metaclasses/IRPYRawContainer/IPropertyMetaclass/_Name/text()")
                if len(stereotype_node) > 0:
                    cgiclass["stereotype"] = stereotype_node[0]

                # Get parent
                parent_node = cgi.xpath("m_pParent/text()")
                assert len(parent_node) == 1
                cgiclass["parent"] = parent_node[0]


                classes[id] = cgiclass
                print id, "Class:", cgiclass

        diagramdata["classes"] = classes

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
            print "Assoc:", assoc["source"], sourcerole, " - ", assoc["target"], targetrole
            associations.append(assoc)
        diagramdata["associations"] = associations

        # Packages
        packages = []
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIPackage"):
            pkg_node = cgi.xpath("m_name/CGIText/m_str/text()")
            if len(pkg_node) > 0:
                name = pkg_node[0]
                id_node = cgi.xpath("_id/text()")
                assert len(id_node) == 1
                id = id_node[0]

                print "Package:", name
                pkg = {}
                pkg["name"] = name
                pkg["includes"] = []
                for classid in classes:
                    if classes[classid]["parent"] == id:
                        pkg["includes"].append(classes[classid]["name"])

                packages.append(pkg)
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

            inherit = {}
            inherit["source"] = classes[source]["name"]
            inherit["target"] = classes[target]["name"]
            print "Inherit:", inherit["source"], " - ", inherit["target"]
            inheritance.append(inherit)
        diagramdata["inheritance"] = inheritance

    # Done
    return diagramdata


def find_nearest_lifeline(position):
    global data_lifelines
    # Start with large diff and unknown participant
    smallest_dist = 99999999
    smallest_part = None

    for key, part in sorted(data_lifelines.iteritems(), key=lambda kvt: kvt[1].position.top_left_x):
        if smallest_part == None:
            smallest_part = part

        dist = abs(part.position.get_center_x() - position.get_center_x())
        logging.debug("Nearest lifeline: Check: %s against %s", dist, smallest_dist)

        if smallest_dist < dist:
            return smallest_part
        else:
            smallest_part = part
            smallest_dist = dist
    return smallest_part

def quote_if_space(string):
    if " " in string:
        return '"%s"' % (string)
    else:
        return string

def quote_if_text(string):
    if len(string) > 0:
        return '"%s"' % (string)
    else:
        return string

def generate_plantuml(chartdata):
    global data_lifelines

    print "@startuml"
    print "hide footbox"
    print "title", chartdata["name"]
    print ""

    # Print order of participants
    for key, part in sorted(data_lifelines.iteritems(), key=lambda kvt: kvt[1].position.top_left_x):
        color = ""
        if part.fillstyle != 0:
            color = "#F5F5F5"

        if part.type == PartType.ACTOR:
            print 'actor %s %s' % (quote_if_space(part.name), color)
        else:
            print 'participant %s %s' % (quote_if_space(part.name), color)

        logging.debug("Position: %s", part.position)
    print ""

    # Print all events(messages/conditions and more)
    for event in sorted(chartdata["events"], key=lambda x: x.position.top_left_y):
        logging.debug("Print events: %s", event)

        # Handle messsage arrows
        if event.type == EventType.MESSAGE:
            arrow = "->"
            if event.type == MessageType.REPLY:
                arrow = "-->"
                
            print '%s %s %s : %s(%s)' % (quote_if_space(data_lifelines[event.sender].name),
                                       arrow,
                                       quote_if_space(data_lifelines[event.receiver].name),
                                       event.name, event.args)

        elif event.type == EventType.COND_START:
            print event.cond, event.text

        elif event.type == EventType.COND_ELSE:
            print event.cond, event.text

        elif event.type == EventType.COND_END:
            print "end"

# TODO: span over many lifelines
        elif event.type == EventType.NOTE:
            participant = find_nearest_lifeline(event.position)
            text = event.text
            if '\n' in text:
                # Handle multiline notes
                print 'note over %s' % (participant.name)
                print text
                print 'end note'
            else:
                print 'note over %s: %s' % (participant.name, text)

# TODO: span over many lifelines
        elif event.type == EventType.REF:
            participant = find_nearest_lifeline(event.position)
            text = event.text
            if '\n' in text:
                # Handle multiline reference
                print 'ref over %s' % (participant.name)
                print text
                print 'end ref'
            else:
                print 'ref over %s : %s' % (participant.name, text)

        elif event.type == EventType.DIVIDER:
            print "==", event.text, "=="

        logging.debug("Position: %s", event.position)

    print "@enduml"



def generate_plantuml_classdiagram(diagram):
    print "" 
    print "@startuml"
    print "title", diagram["name"]
    print ""

    for id in diagram["classes"]:

        # Check if included in a package
        add_pkg_end = None
        for pkg in diagram["packages"]:
            for name in pkg["includes"]:
                if name == diagram["classes"][id]["name"]:
                    print "package %s {" % (pkg["name"])
                    add_pkg_end = 1

        if "stereotype" in diagram["classes"][id]:
            type = "class"
            if diagram["classes"][id]["stereotype"] == "Interface":
                type = "interface"

            print "%s %s <<%s>>" % (type,
                                    diagram["classes"][id]["name"],
                                    diagram["classes"][id]["stereotype"])
        elif add_pkg_end:
            print "  class", diagram["classes"][id]["name"]

        if add_pkg_end:
            print "}"


    for data in diagram["inheritance"]:
        print data["target"], "<|--", data["source"]

    for data in diagram["associations"]:
#        print "%s %s--> %s %s" % (data["source"], quote_if_text(data["sourcerole"]),
#                                  quote_if_text(data["targetrole"]), data["target"])
        print "%s %s--> %s %s : %s" % (data["source"], quote_if_text(data["sourcemultiplicity"]),
                                  quote_if_text(data["targetmultiplicity"]), data["target"],
                                  data["targetrole"])


    print "@enduml"
    print ""



def generate_plantuml_usecase(ucdata, diagram):
    for name in diagram:
        print "@startuml"
        print "title", name
        print "left to right direction"
        print ""

        # Print actor (todo: only once!!)
        actors = []
#        for uc_guid in diagram[name]['free_ucs']:
#            actors.append(global_participants[uc_guid].name.replace(" ","_"))

        for rect in diagram[name]['rect_ucs']:
            for uc in diagram[name]['rect_ucs'][rect]['ucs']:
                # Add actors associated by usecase
                for assoc in ucdata[uc]['associations']:
                    actors.append(global_participants[assoc].name.replace(" ","_"))

                # Add actors that associates to the usecase
                for guid in global_participants:
                    # Arrow is a dependency?
                    for uc_guid in global_participants[guid].dependencies:
                        if uc_guid == uc:
                            actors.append(global_participants[guid].name.replace(" ","_"))
                            # Add actor to the usecase
                            if guid not in ucdata[uc]['dependencies']:
                                ucdata[uc]['dependencies'].append(guid)

                    # Arrow is a association?
                    for uc_guid in global_participants[guid].associations:
                        if uc_guid == uc:
                            actors.append(global_participants[guid].name.replace(" ","_"))
                            # Add actor to the usecase
                            if guid not in ucdata[uc]['associations']:
                                ucdata[uc]['associations'].append(guid)


        # remove duplicates
        actors = list(set(actors))
        for actor in actors:
            print 'actor', actor
        print ""

        # Get sequencediagram (can be within a usecase as well! Searching for tag only)
        charts = {}
        charts[""] = ""
        for chart in root.xpath(".//IMSC"):
            id = chart.xpath("_id/text()")[0]
            charts[id] = chart.xpath("_name/text()")[0]
            

        # Adding global usecases
        for uc in diagram[name]['free_ucs']:
            for assoc in ucdata[uc]['associations']:
                print '%s -- (%s  [[%s]])' % (global_participants[assoc].name.replace(" ","_"), ucdata[uc]['name'], charts[ucdata[uc]['statechart']])
# TODO: dependency to other usecase

#            for assoc in ucdata[uc]['dependencies']:
#                print assoc
#                print '%s -- (%s  [[%s]])' % (global_participants[assoc].name.replace(" ","_"), ucdata[uc]['name'], charts[ucdata[uc]['statechart']])

        # Adding boxes with usecases
        for rect in diagram[name]['rect_ucs']:
            rect_name = diagram[name]['rect_ucs'][rect]['name']
            rect_ucs = diagram[name]['rect_ucs'][rect]['ucs']
            logging.debug("%s %s", rect_name, rect_ucs)

            print 'rectangle %s {' % quote_if_space(rect_name)
            for uc in rect_ucs:
                for assoc in ucdata[uc]['associations']:
                    print '  %s -- (%s  [[%s]])' % (global_participants[assoc].name.replace(" ","_"), ucdata[uc]['name'], charts[ucdata[uc]['statechart']])
                for dep in ucdata[uc]['dependencies']:
                    if dep in global_participants:
                        print '  %s -- (%s  [[%s]])' % (global_participants[dep].name.replace(" ","_"), ucdata[uc]['name'], charts[ucdata[uc]['statechart']])
                        
            print "}"

        print "@enduml"
        print ""


def print_usecase_list(xmlnode):
    print "Usecase diagrams:" 
    for usecase in xmlnode.findall(".//ISubsystem/Declaratives/IRPYRawContainer/IUCDiagram"):
        name = usecase.xpath("_name/text()")[0]
        print "  ", name


def print_sequencediagrams_list(xmlnode):
    print "Sequence diagrams:" 
    for diagram in xmlnode.findall(".//IMSC"):
        name = diagram.xpath("_name/text()")[0]
        print "  ", name

def print_classdiagram_list(xmlnode):
    print "Object and Class Diagrams:" 
    for diagram in xmlnode.findall(".//ISubsystem/Declaratives/IRPYRawContainer/IDiagram"):
        name = diagram.xpath("_name/text()")[0]
        print "  ", name


if __name__ == "__main__":
    parser = ArgumentParser(formatter_class = ArgumentDefaultsHelpFormatter)
    parser.add_argument("file", help="XML file to parse")
    parser.add_argument("-v", dest="verbose", help="Enable verbose log", action="store_true")
    parser.add_argument("-l", "--list", dest="list", help="List extractable charts", action="store_true")
    parser.add_argument("-s", dest="sequence", help="Name of sequence diagram to generate to PlantUML")
    parser.add_argument("-u", dest="usecase", help="Name of usecase diagram to generate to PlantUML")
    parser.add_argument("-c", dest="classdiagram", help="Name of class or object diagram to generate to PlantUML")
    options = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)

    tree = etree.parse(options.file)
    root = tree.getroot()

    if options.list:
        print_usecase_list(root)
        print_sequencediagrams_list(root)
        print_classdiagram_list(root)
        sys.exit()

    # Parse global info
    parse_classes(root)
    parse_actors(root)

    # Parse sequence diagram
    if options.sequence:
        seqdata = parse_sequencediagram(root, options.sequence)
        generate_plantuml(seqdata)

    # Parse usecase
    elif options.usecase:
        ucdata, diagram = parse_usecases(root, options.usecase)
        generate_plantuml_usecase(ucdata, diagram)

    # Parse class
    elif options.classdiagram:
        data = parse_classdiagram(root, options.classdiagram)
        generate_plantuml_classdiagram(data)

    else:
        print "No action given"

    sys.exit()
