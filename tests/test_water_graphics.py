from dataclasses import replace
from types import SimpleNamespace
import math
from tank.art import fish_model, expressed_colour
from tank.water_art import animate_water

def snap(species=0,stage=2,**kw):
    return SimpleNamespace(owner='a'*64,stage=stage,body=0,scales=4,eyes=2,tint=65535,kind='snapshot',species_id=species,**kw)

def test_all_models_stages_and_low_detail():
    for stage in range(4):
        for species in range(14):
            model,tail,fins=fish_model(snap(species,stage),8)
            assert not model.isEmpty() and not tail.isEmpty()
            assert model.findAllMatches('**/+GeomNode').getNumPaths()>0
            if species:
                before=[tuple(n.getHpr()) for n in fins]
                animate_water(model,tail,fins,1.2,1.)
                assert any(tuple(n.getHpr())!=p for n,p in zip(fins,before))
                assert all(math.isfinite(v) for n in fins for v in n.getHpr())
            model.removeNode()

def test_fallback_and_genes():
    a=fish_model(snap(0),8)[0];b=fish_model(snap(65000),8)[0]
    assert a.getName()==b.getName() and not b.hasTag('water-species')
    assert expressed_colour(snap(body_gene=8),'body')==(1.,0.,0.)
    assert expressed_colour(snap(body_gene=88),'body')==(0.,1.,0.)
    assert expressed_colour(snap(body_gene=255),'body')==expressed_colour(snap(),'body')
    a.removeNode();b.removeNode()

def test_juvenile_neutral_eyes_and_replacement():
    for species in range(1,14):
        a=fish_model(snap(species,0,eyes_gene=8),8)[0]
        b=fish_model(snap(species,0,eyes_gene=168),8)[0]
        # Flattened geometry must have the same vertex colours for eye changes.
        def colours(node):
            from panda3d.core import GeomVertexReader
            result=[]
            for path in node.findAllMatches('**/+GeomNode'):
                gn=path.node()
                for g in range(gn.getNumGeoms()):
                    rd=GeomVertexReader(gn.getGeom(g).getVertexData(),'color')
                    while not rd.isAtEnd(): result.append(tuple(rd.getData4()))
            return result
        assert colours(a)==colours(b)
        a.removeNode();b.removeNode()
