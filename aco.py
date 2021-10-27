import igraph as ig
import random
import copy

alfa = 0.8
beta = 0.17
p = 0.1

def read_file(file_name):
    f = open(file_name, "r")
    n_jobs, n_machines = [int(valor) for valor in f.readline().split()]

    operations = []

    for i in range(1, n_jobs+1):
        line = f.readline().split()

        for j in range(0, n_machines*2, 2):
            operations.append( (i, int(line[j]), int(line[j+1])) )

    f.close()
    return n_jobs, n_machines, operations

def create_dictionary(operations):
    dictionary = {}
    for idx,operation in enumerate(operations):
        dictionary[idx] = operation
    
    return dictionary

# operations sequence of each job
def create_sequence(n_jobs,n_machines,operations):
    sequences = []
    start = 0
    stop = n_machines
    
    for _ in range(n_jobs):
        sequences.append(operations[start:stop])
        
        start = stop
        stop += n_machines
    
    return sequences

# edges that constraint operation is not mainted
def delete_edges(g,n_jobs,n_machines):
    # edges between operations of job
    start = 0
    end = n_machines

    for _ in range(n_jobs):
        j = start

        for _ in range(n_machines-1):
            for idx,i in enumerate(range(j,end-1)):
                # delete infeasible edges
                e_id = g.get_eid(i+1,j)
                g.delete_edges(e_id)
                
                if idx != 0:
                    e_id = g.get_eid(j,i+1)
                    g.delete_edges(e_id)      
            
            j += 1
    
        start = end
        end += n_machines

def evaluate_makespan(path,operations_dict,n_jobs,n_machines):
    print(path)
    # transform path to operations
    operations = [operations_dict[i] for i in path]

    print(operations)
    
    # each machine has a end time
    machine_time = [0 for _ in range(n_machines)]

    # more recent end time of the job
    job_time = [0 for _ in range(n_jobs)]

    for operation in operations:
        job,machine,time = operation

        max_time = max(machine_time[machine],job_time[job-1])

        machine_time[machine] = max_time + time
        job_time[job-1] = machine_time[machine]
    
    # job that has the max time to complete
    makespan = max(job_time)
    return makespan

def update_evaporating():
    pass

def update_pheromone():
    pass

def roulette_wheel(g,origin_vertex,feasible_vertices,operations_dict):
    # pheromone trail and heuristic information importance
    importances = []
    
    for destiny_vertex in feasible_vertices:
        e_id = g.get_eid(origin_vertex,destiny_vertex)
        
        weight = g.es[e_id]["weight"]
        operation_time = operations_dict[destiny_vertex][2]
        
        vertex_importance = (weight**alfa) * ((1/operation_time)**beta)
        importances.append(vertex_importance)

    probabilities = []
    importances_sum = sum(importances)

    print("importances:",importances)
    
    for importance in importances:
        probability = importance / importances_sum
        probabilities.append(probability)

    print("probabilities:",probabilities)
    selection = random.choices(feasible_vertices, weights=probabilities, k=1)
    return selection[0]

def create_path(g,n_jobs,n_machines,sequence,operations_dict):
    # visited vertices -> ant path
    tabu = []
    tabu_full = n_jobs*n_machines
    
    # put the ant into a random first feasible vertex
    first_operations = [n_machines*i for i in range(n_jobs)]
    op = random.choice(first_operations)
    tabu.append(op)

    print("primeira operacao:",op)

    idx_job = op // n_machines
    sequence[idx_job].pop(0)

    while len(tabu) < tabu_full:
        vertex = g.vs[op]
        neighbors = g.successors(vertex)

        # feasible operations -> probably path
        feasible = []
        
        for neighbor in neighbors:
            vertex_index = g.vs[neighbor].index
            if  vertex_index not in tabu:
                # add some usefull comment here
                idx_job = vertex_index // n_machines
                operation = operations_dict[vertex_index]
                feasible_operation = sequence[idx_job][0]

                if operation == feasible_operation:
                    index = g.vs[neighbor].index
                    feasible.append(index)
                
        print("feasibles:", feasible)
        # decides which vertex the ant gonna choose
        vertex_selected = roulette_wheel(g,vertex,feasible,operations_dict)
        op = vertex_selected
        print("operacao selecionada:",op)
        # op = random.choice(feasible)
        tabu.append(op)

        print("tabu:", tabu)

        x = input()

        # Tem que dar um pop em SEQUENCE na operacao que foi utilizada
        idx_job = op // n_machines
        sequence[idx_job].pop(0)
    
    return tabu

def execute(g,n_jobs,n_machines,sequence,operations_dict):
    # definir os valores iniciais do algoritmo
    # do feromonio, evaporacao
    alfa = 0.8
    beta = 0.17
    p = 0.1

    cycle = 10
    n_ants = 2
    
    # each ant has a path
    ants = []
    
    for _ in range(n_ants):
        sequence_copy = copy.deepcopy(sequence)
        ant = create_path(g,n_jobs,n_machines,sequence_copy,operations_dict)
        ants.append(ant)
    
    print(ants)

def main():
    file = "datasets//teste.txt"
    n_jobs, n_machines, operations = read_file(file)

    operations_dict = create_dictionary(operations)
    sequence = create_sequence(n_jobs,n_machines,operations)

    size_graph = n_jobs*n_machines
    g = ig.Graph.Full(n=size_graph, directed=True)
    
    delete_edges(g,n_jobs,n_machines)

    # pesquisar aqui qual o melhor valor de feromonio inicial para as arestas
    g.es["weight"] = [0.1]
    
    execute(g,n_jobs,n_machines,sequence,operations_dict)

    # makespan = evaluate_makespan(path,operations_dict,n_jobs,n_machines)
    # print(makespan)

main()