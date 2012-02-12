from esdlc.model import FluentSystem

class Test1(FluentSystem):
    ESDL_DEF = '''size = 100.0
FROM random_binary(length=10.0) SELECT (size) population
EVAL population USING default_evaluator()
YIELD population

BEGIN generation
    FROM population SELECT (size) parents USING tournament(k=2.0)
    FROM parents SELECT offspring USING mutate_random(per_gene_rate=0.1)
    FROM population, offspring SELECT (size) population USING best()
    YIELD population
END generation'''
    
    def definitions(self):
        self.External("random_binary")
        self.External("default_evaluator")
        self.External("tournament")
        self.External("mutate_random")
        self.External("best")
        
        self.Group("population")
        self.Group("parents")
        self.Group("offspring")

        self.Variable("size")

        self.Block('generation')
    
    def block_init(self):
        self.Assign("size", 100.0)

        self.From(self.Generator("random_binary", length=10.0)) \
            .Select(self.Group("population", "size"))

        self.Eval("population", "default_evaluator")
        self.Yield("population")

    def block_generation(self):
        self.From("population") \
            .Select(self.Group("parents", limit="size")) \
            .Using(self.Function("tournament", k=2.0))
        self.From("parents") \
            .Select("offspring") \
            .Using(self.Function("mutate_random", per_gene_rate=0.1))

        self.From("population", "offspring") \
            .Select(self.Group("population", limit="size")) \
            .Using("best")

        self.Yield("population")

class Test2(FluentSystem):
    ESDL_DEF = '''size = 100.0
FROM random_binary(length=10.0) SELECT (size) population
YIELD population

BEGIN generation
    FROM population SELECT (size) parents USING tournament(k=2.0)
    REPEAT 10.0
        FROM parents SELECT (1) offspring USING random_shuffle(), mutate_random(per_gene_rate)
        FROM population, offspring SELECT (size) population USING best()
    END REPEAT
    YIELD population
END generation'''
    
    def definitions(self):
        self.External("random_binary")
        self.External("default_evaluator")
        self.External("tournament")
        self.External("random_shuffle")
        self.External("mutate_random")
        self.External("best")

        self.Group("population")
        self.Group("parents")
        self.Group("offspring")

        self.Variable("size")

        self.Block('generation')
    
    def block_init(self):
        self.Assign("size", 100.0)

        self.From(self.Generator("random_binary", length=10.0)) \
            .Select(self.Group("population", limit="size"))
        self.Yield("population")

    def block_generation(self):
        self.From("population") \
            .Select(self.Group("parents", limit="size")) \
            .Using(self.Function("tournament", k=2.0))
        
        self.Repeat(self.subblock_generation, 10.0)
        
        self.Yield("population")

    def subblock_generation(self):    
        self.From("parents") \
            .Select(self.Group("offspring", limit=1.0)) \
            .Using("random_shuffle",
                   self.Function("mutate_random", per_gene_rate=None))

        self.From("population", "offspring") \
            .Select(self.Group("population", limit="size")) \
            .Using("best")

class Test3(FluentSystem):
    ESDL_DEF = '''FROM random_binary(length=config.length.max) SELECT (100) population
t = 0
delta_t = (-0.1)
EVAL population USING evaluators.population(t)
YIELD population

BEGIN generation
    t = (t+(delta_t*1.4))
    `print t
    REPEAT 10
        FROM population SELECT (100) parents USING tournament(k=2, greediness=0.7)
        FROM parents SELECT mutated USING mutate_delta(stepsize)
        FROM parents SELECT crossed USING uniform_crossover()
        EVAL mutated, crossed USING evaluator(t=t)
        JOIN mutated, crossed INTO merged USING tuples()
        FROM merged SELECT offspring USING best_of_tuple()
        FROM population, offspring SELECT (99) population, rest USING best()
        FROM rest SELECT (1) extras USING uniform_random()
        FROM population, rest, extras SELECT (100) population
    END REPEAT
    EVAL population USING evaluators.config(t)
    YIELD population
END generation'''
    
    def definitions(self):
        self.External("config")
        self.External("evaluators")
        self.Function("random_binary")
        self.Function("tournament")
        self.Function("mutate_delta")
        self.Function("uniform_crossover")
        self.Function("tuples")
        self.Function("best_of_tuple")
        self.Function("best")
        self.Function("uniform_random")

        self.Variable("t")
        self.Variable("delta_t")
        self.Variable("stepsize")

        self.Group("population")
        self.Group("parents")
        self.Group("mutated")
        self.Group("crossed")
        self.Group("merged")
        self.Group("offspring")
        self.Group("rest")
        self.Group("extras")
        
        self.Block("generation")

    def block_init(self):
        '''FROM random_binary(length=config.length.max) SELECT (100) population
        t = 0
        delta_t = (-0.1)
        EVAL population USING evaluators.population(t)
        YIELD population
        '''
        self.From(self.Generator("random_binary", length=self.RPNExpression("config length . max ."))) \
            .Select(self.Group("population", limit=100))

        self.Assign("t", 0)
        self.Assign("delta_t", self.RPNExpression("0.1 -"))

        self.Eval("population", self.Function(self.RPNExpression("evaluators population ."), t=None))
        self.Yield("population")
                
    def block_generation(self):
        '''BEGIN generation
            t = (t+(delta_t*1.4))
            `print t
            REPEAT 10
                ...
            END REPEAT
            EVAL population USING evaluators.config(t)
            YIELD population
        END generation
        '''

        self.Assign('t', self.RPNExpression("t delta_t 1.4 * +"))
        self.Pragma('print t')

        self.Repeat(self.repeat_block, 10)

        self.Eval("population", self.Function(self.RPNExpression("evaluators config ."), t=None))
        self.Yield("population")

    def repeat_block(self):
        '''FROM population SELECT (100) parents USING tournament(k=2, greediness=0.7)
        FROM parents SELECT mutated USING mutate_delta(stepsize)
        FROM parents SELECT crossed USING uniform_crossover()
        EVAL mutated, crossed USING evaluator(t=t)
        JOIN mutated, crossed INTO merged USING tuples()
        FROM merged SELECT offspring USING best_of_tuple()
        FROM population, offspring SELECT (99) population, rest USING best()
        FROM rest SELECT (1) extras USING uniform_random()
        FROM population, rest, extras SELECT (100) population
        '''
        self.From("population").Select(self.Group("parents", limit=100)) \
            .Using(self.Function("tournament", k=2, greediness=0.7))

        self.From("parents").Select("mutated").Using(self.Function("mutate_delta", stepsize=None))
        self.From("parents").Select("crossed").Using("uniform_crossover")

        self.Eval("mutated", "crossed", self.Function("evaluator", t="t"))

        self.Join("mutated", "crossed").Into("merged").Using("tuples")
        self.From("merged").Select("offspring").Using("best_of_tuple")
        
        self.From("population", "offspring").Select(self.Group("population", limit=99), "rest").Using("best")

        self.From("rest").Select(self.Group("extras", limit=1)).Using("uniform_random")

        self.From("population", "rest", "extras").Select(self.Group("population", limit=100))

def check(system_cls):
    system = system_cls()
    validation = system.validate()
    print 'Errors:\n  ' + '\n  '.join(str(i) for i in validation.errors)
    print 'Warnings:\n  ' + '\n  '.join(str(i) for i in validation.warnings)
    code = system.as_esdl()
    assert code.strip(' \n\r\t') == system.ESDL_DEF.strip(' \n\r\t'), \
        "Actual: \n" + code

def test_esdl_emit():
    for cls in [Test1, Test2, Test3]:
        yield check, cls
