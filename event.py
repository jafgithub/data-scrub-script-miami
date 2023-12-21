"""
    Event class is a dict inherited custom class used to define events. 
    This class also has default values used for fields which are default.
"""

from utils import create_unique_object_id

class Event(dict):

    """
        Event class used to represent an event object has 32 fields.
    """
    def __init__(self, *args, **kwargs):
        
        id = create_unique_object_id()
        default_data = {
            "id" : id,
            "UID" : 4,
            "cid" : 1,
            "title" : "",
            "img" : "",
            "cover_img" : "",
            "sdate" : "",
            "stime" : "",
            "etime" : "",
            "address" : "",
            "status" : 1,
            "description" : "",
            "disclaimer" : "",
            "latitude" : "",
            "longitude" : "",
            "is_booked" : 0,
            "event_status" : "Completed",
            "place_name" : "",
            "ticket_id" : id,
            "eid" : id,
            "event category" : "",
            "price" : 0.00,
            "ticket_tlimit" : 1000,
            "ticket_status" : 1,
            "ticket_booked" : 0,
            "is_soldout" : "FALSE",
            "is_free" : "NONE",
            "address_url" : "NONE",
            "organizer" : "NONE",
            "event_url" : "",
            "edate" : "",
            "original_img_name" : ""
        }
        
        # if kwargs.get('data'):
        #     default_data.update(**kwargs['data'])

        super().__init__(*args, **default_data)
        
        del default_data    #removing as it's of no use now