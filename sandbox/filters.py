def process_filters(event_type, event_data, depth=0):
    for filter in filters:
        if filter.active:
            filter.depth += depth
            if filter.handlers[event_type]:
                status = filter.handlers[event_type](*event_data)
            else:
                status = filter.default
            if status == ExpatFilter.HANDLED:
                break
        elif criteria.matches(event_type, event_data):
            filter.active = True
            if filter.handlers[START_FILTER]:
                filter.handlers[START_FILTER](*event_data)
            break
    return

def startDocument():
    for filter in filters:
        if filter.active:
            filter.depth += 1
            if filter.startDocument:
                status = filter.startDocument()
            else:
                status = filter.defaultHandler()
            if status == ExpatFilter.HANDLED:
                break
        elif criteria.matches(event_type, event_data):
            filter.active = True
            if filter.startFilter:
                filter.startFilter(*event_data)
            break
def endDocument():
    process_filters(END_DOCUMENT, (), -1)
def startElement(*args):
    process_filters(START_ELEMENT, args, 1)
def endElement(*args):
    process_filters(END_ELEMENT, args, -1)
def characters(*args)
    process_filters(CHARACTERS, args)
def ignorableWhitespace(*args):
    process_filters(IGNORABLE_WHITESPACE, args)


class simple_string_element(HandlerType):
    def start_filter(self, expandedName, tagName):
        self.value = []

    def end_filter(self, expandedName, tagName):
        # Its possible that the parentNode may already have an attribute of the
        # same name (via a child element).
        value = u''.join(self.value)
        self.chain_next.attribute(expandedName, tagName, value)

    def start_element(self, expandedName, tagName, attributes):
        warn()

    def characters(self, data):
        self.value.append(data)


class omit_element(HandlerType):
    """Drops all descendant events"""


class element_skeleton(FilterType):
    """Drops all character data for the matching element and descendants"""
    def characters(self, data):
        pass
    def whitespace(self, data):
        pass


class ws_strip_element(FilterType):
    """Drops all ignorable whitespace for the matching element and descendants"""
    def whitespace(self, data):
        pass


class ws_preserve_element(FilterType):
    """Converts ignorable whitespace into regular character data"""
    def whitespace(self, data):
        self.chain_next.characters(data)


class type_inference(FilterType):
    """Stores attributes as a more specific type"""
    def start_element(self, expandedName, tagName, attributes):
        for key, value in attributes.items():
            value = infer_data_from_string(value)
            if value is not None:
                attributes[key] = value
        self.chain_next.start_element(expandedName, tagName, attributes)

    def attribute(self, expandedName, name, value):
        typed_value = infer_data_from_string(value)
        if typed_value is not None:
            value = typed_value
        self.chain_next.attribute(expandedName, name, value)
