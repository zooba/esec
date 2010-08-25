import StringIO
from nose.tools import raises
from esec.utils import safe_div, ConfigDict

def test_safe_div():
    assert safe_div(4,2) == 2
    assert safe_div(1,0) == 0


# a subclass to make sure it works
class MyCFG(ConfigDict):
    
    #__slots__ = ('_dict',)
    syntax = "syntax"
    
    def __init__(self, data=None):
        super(MyCFG, self).__init__(data)
        self.name = "Fred" # <- stored in self._dict not self.__dict__
        
    def method_A(self):
        return "A"

d1 = {'k1': 123, 
      'k2':'v2',
      'k3':{'sk1': 'sv1', 'sk2': 'sv2'},
      'k4': True,}

def test_ConfigDict_access():
    # create a normal dict, feed to ConfigDict
    cfg = ConfigDict(d1)
    
    # check item access
    assert cfg['k2'] == 'v2'
    cfg['k2'] = '*v2'
    assert cfg['k2'] == '*v2'
    
    # check nested item access
    assert cfg['k3']['sk2'] == 'sv2'
                      
    # check attribute access
    assert cfg.k1 == 123
    cfg.k4 = '*v4'
    assert cfg.k4 == '*v4'
    assert cfg['k4'] == '*v4'
    # check nested attribute access
    assert cfg.k3.sk1 == 'sv1'
    
    # check access created attribute to key
    cfg.name = 'Mary'
    cfg.name = 'Fred'
    assert cfg.name == 'Fred'
    assert cfg['name'] == cfg.name, 'Key=Item mismatch?'

def test_ConfigDict_validate():
    # check type validate, missing error, unknown warning, optional key ?, any value *
    d1 = {'a': 123, 'b': 12.34, 'c': 's', 'd': 1234,  'x': 123,            'w': 1.0}
    s1 = {'a': int, 'b': float, 'c': str, 'd': float, 'y': int, 'z?': int, 'w?': '*' }
    #   syntax issues     ---->         type-> ^^^^^  ^^^         ^          ^   ^^^ 
    cfg1 = ConfigDict(d1)
    errs, warns = cfg1.validate(s1)
    assert len(errs) == 2 and len(warns) == 1

    # valid and nested, keyword sets
    d2 = {'a':'s', 'b': 123, 'n': {'n1': 's', 'n2': 12.34}, 'k1': 'OK',    'k2': 'BAD'}
    s2 = {'a':str, 'b': int, 'n': {'n1': str, 'n2': int},   'k1': ('OK',), 'k2': ('OK',)}
    #   two issues ------>                          ^^^^^             bad keyword ^^^^^
    # should show nested validation issue and set issue
    cfg2 = ConfigDict(d2)
    errs, warns = cfg2.validate(s2)
    assert len(errs) == 2 and len(warns) == 0


def test_ConfigDict_overlay():
    # overlay
    cfg1 = ConfigDict({'a':1, 'b':2, 'c':{'x':1, 'y':2}})
    cfg2 = ConfigDict({'f':8, 'b':3, 'c':{'x':5, }})
    assert str(cfg1) == '{a:1, b:2, c:{x:1, y:2}}', str(cfg1)
    assert str(cfg2) == '{b:3, c:{x:5}, f:8}', str(cfg2)
    assert (cfg1 == cfg2) == False
    cfg3 = ConfigDict(cfg1)
    assert (cfg1 == cfg3) == True
    cfg4 = cfg1 + cfg2
    cfg1 += cfg2
    assert (cfg4 == cfg1) == True

def test_ConfigDict_subclass():
    # subclass??
    mcfg1 = MyCFG()
    assert mcfg1.name == 'Fred'
    assert mcfg1.name == mcfg1['name']
    mcfg1.age = 12
    assert mcfg1.age == 12 and mcfg1['age'] == 12
    mcfg1['size'] = 12.3
    assert mcfg1.size == 12.3 and mcfg1['size'] == 12.3
    assert mcfg1.method_A() == 'A'
    assert mcfg1.syntax == 'syntax'



    