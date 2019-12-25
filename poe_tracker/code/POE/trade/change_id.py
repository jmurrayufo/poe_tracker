
import requests

class ChangeID:


    def __init__(self, *args):
        self.ids = [1,1,1,1,1]
        if len(args) == 5:
            for idx in range(5):
                self.ids[idx] = int(args[idx])
        elif len(args) == 1 and type(args[0]) in (list,tuple) and len(args[0]) == 5:
            for idx in range(5):
                self.ids[idx] = int(args[0][idx])
        elif len(args) == 1 and type(args[0]) == str:
            self.ids = [int(float(i)) for i in args[0].split("-")]
        elif len(args) == 1 and type(args[0]) == type(self):
            for idx in range(5):
                self.ids[idx] = args[0].ids[idx]
        elif len(args) == 0:
            pass
        else:
            raise TypeError


    def sync_poe_ninja(self):
        """Pull current value from poe.ninja/stats
        """
        request = requests.get("https://poe.ninja/api/Data/GetStats")
        request.raise_for_status()
        data = request.json()
        self.ids = [int(i) for i in data['next_change_id'].split("-")]


    def __str__(self):
        return f"{'-'.join(str(i) for i in self.ids)}"
    def __repr__(self):
        return f"ChangeID({','.join(str(i) for i in self.ids)})"


    def __lt__(self, other):
        if type(other) is ChangeID:
            return all( [ a<b for a,b in zip(self.ids,other.ids)] )
        elif type(other) in [float,int]:
            return all( [ a<other for a in self.ids] )
        return NotImplemented(f"Cannot compare ChangeID to {type(other)}")
    def __le__(self, other):
        if type(other) is ChangeID:
            return all( [ a<=b for a,b in zip(self.ids,other.ids)] )
        elif type(other) in [float,int]:
            return all( [ a<=other for a in self.ids] )
        return NotImplemented(f"Cannot compare ChangeID to {type(other)}")
    def __eq__(self, other):
        if type(other) is ChangeID:
            return all( [ a==b for a,b in zip(self.ids,other.ids)] )
        elif type(other) in [float,int]:
            return all( [ a==other for a in self.ids] )
        return NotImplemented(f"Cannot compare ChangeID to {type(other)}")
    def __ne__(self, other):
        if type(other) is ChangeID:
            return any( [ a!=b for a,b in zip(self.ids,other.ids)] )
        elif type(other) in [float,int]:
            return any( [ a!=other for a in self.ids] )
        return NotImplemented(f"Cannot compare ChangeID to {type(other)}")
    def __gt__(self, other):
        if type(other) is ChangeID:
            return all( [ a>b for a,b in zip(self.ids,other.ids)] )
        elif type(other) in [float,int]:
            return all( [ a>other for a in self.ids] )
        return NotImplemented(f"Cannot compare ChangeID to {type(other)}")
    def __ge__(self, other):
        if type(other) is ChangeID:
            return all( [ a>=b for a,b in zip(self.ids,other.ids)] )
        elif type(other) in [float,int]:
            return all( [ a>=other for a in self.ids] )
        return NotImplemented(f"Cannot compare ChangeID to {type(other)}")


    def __add__(self, other):
        if type(other) == type(self):
            return ChangeID([a+b for a,b in zip(self.ids, other.ids)])
        if type(other) in [int,float]:
            return ChangeID([a+other for a in self.ids])
    def __iadd__(self, other):
        if type(other) == type(self):
            self.ids[0] += other.ids[0]
            self.ids[1] += other.ids[1]
            self.ids[2] += other.ids[2]
            self.ids[3] += other.ids[3]
            self.ids[4] += other.ids[4]
        if type(other) in [int,float]:
            self.ids[0] += other
            self.ids[1] += other
            self.ids[2] += other
            self.ids[3] += other
            self.ids[4] += other
    def __radd__(self, other):
        return self.__add__(other)


    def __sub__(self, other):
        if type(other) == type(self):
            return ChangeID([a-b for a,b in zip(self.ids, other.ids)])
        if type(other) in [int,float]:
            return ChangeID([a-other for a in self.ids])
    def __isub__(self, other):
        if type(other) == type(self):
            self.ids[0] -= other.ids[0]
            self.ids[1] -= other.ids[1]
            self.ids[2] -= other.ids[2]
            self.ids[3] -= other.ids[3]
            self.ids[4] -= other.ids[4]
        if type(other) in [int,float]:
            self.ids[0] -= other
            self.ids[1] -= other
            self.ids[2] -= other
            self.ids[3] -= other
            self.ids[4] -= other


    def __mul__(self, other):
        if type(other) == type(self):
            return ChangeID([a*b for a,b in zip(self.ids, other.ids)])
        if type(other) in [int,float]:
            return ChangeID([a*other for a in self.ids])
    def __imul__(self, other):
        if type(other) == type(self):
            self.ids[0] *= other.ids[0]
            self.ids[1] *= other.ids[1]
            self.ids[2] *= other.ids[2]
            self.ids[3] *= other.ids[3]
            self.ids[4] *= other.ids[4]
        if type(other) in [int,float]:
            self.ids[0] *= other
            self.ids[1] *= other
            self.ids[2] *= other
            self.ids[3] *= other
            self.ids[4] *= other
    def __rmul__(self, other):
        return self.__mul__(other)


    def __pow__(self, other):
        if type(other) in [int,float]:
            return ChangeID([a**other for a in self.ids])
        return NotImplemented

