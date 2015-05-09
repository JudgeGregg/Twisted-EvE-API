calendar_events_mapping = {
    'action': '/char/UpcomingCalendarEvents.xml.aspx',
    'fields': ['eventID', 'ownerName', 'eventDate', 'eventTitle', 'duration',
               'eventText']
}

contracts_mapping = {
    'action': '/char/Contracts.xml.aspx',
    'fields': ['contractID', 'startStationID', 'status', 'price']
}

contract_items_mapping = {
    'action': '/char/ContractItems.xml.aspx',
    'fields': ['typeID', 'quantity', 'included']
}

corp_contracts_mapping = {
    'action': '/corp/Contracts.xml.aspx',
    'fields': ['contractID', 'startStationID', 'type', 'status', 'price',
               'title']
}

corp_contract_items_mapping = {
    'action': '/corp/ContractItems.xml.aspx',
    'fields': ['typeID', 'quantity', 'included']
}
