class InvalidCookie(Exception): pass

class InvalidOtp(Exception): pass

class InvalidChallangeType(Exception): pass

class Request:
    class Failed(Exception): pass
    
    class InvalidStatus(Exception): pass

class Config:
    class InvalidFormat(Exception): pass

    class MissingValues(Exception): pass

    class CantAccess(Exception): pass


# hi xolo here
# wanted to add a lil comment here °c°

# class x: ... 
# looks much cooler but chatgpt say not good practise :angry: