import igraph as ig
import random
import copy

alfa = 0.8
beta = 0.17
p = 0.1
Q = 1

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
    # print(path)
    # transform path to operations
    operations = [operations_dict[i] for i in path]

    # print(operations)
    
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

def update_pheromone(g,ant_paths,operations_dict,n_jobs,n_machines):
    # all paths has the same size
    size_path = len(ant_paths[0])
    
    for ant_path in ant_paths:
        makespan = evaluate_makespan(ant_path,operations_dict,n_jobs,n_machines)
        """print(ant_path)
        print(makespan)"""

        for i in range(size_path-1):
            origin = ant_path[i]
            destiny = ant_path[i+1]

            e_id = g.get_eid(origin,destiny)
            g.es[e_id]["weight"] += (Q/makespan)
        
def update_evaporating(g):
    new_weights = [(1-p)*weight for weight in g.es["weight"]]
    g.es["weight"] = new_weights

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
    
    for importance in importances:
        probability = importance / importances_sum
        probabilities.append(round(probability,2))

    #print("probabilities:",probabilities)
    selection = random.choices(feasible_vertices, weights=probabilities, k=1)
    return selection[0]

def create_path(g,n_machines,sequence,operations_dict,tabu,tabu_size):
    #print("\nprimeira operacao:",op)

    op = tabu[-1]
    
    while len(tabu) < tabu_size:
        vertex = g.vs[op]
        neighbors = g.successors(vertex)

        # feasible operations -> probably path
        feasible = []
        
        for neighbor in neighbors:
            neighbor_index = g.vs[neighbor].index
            if  neighbor_index not in tabu:
                # add some usefull comment here
                idx_job = neighbor_index // n_machines
                operation = operations_dict[neighbor_index]
                feasible_operation = sequence[idx_job][0]

                if operation == feasible_operation:
                    feasible.append(neighbor_index)
                
        # decides which vertex the ant gonna choose
        vertex_selected = roulette_wheel(g,vertex,feasible,operations_dict)
        op = vertex_selected
        #print("operacao selecionada:",op)
        # op = random.choice(feasible)
        tabu.append(op)

        #print("tabu:", tabu)

        #x = input()

        # pop in the used sequence operation
        idx_job = op // n_machines
        sequence[idx_job].pop(0)
    
    return tabu

def delete_operations(idx_operations,sequence,n_machines):
    for operation in idx_operations:
        idx_job = operation // n_machines
        sequence[idx_job].pop(0)
    
    return sequence

def best_ants(ants_path,n_jobs,n_machines,operations_dict,n_operations):
    idx_value = []
    
    for idx,ant_path in enumerate(ants_path):
        makespan = evaluate_makespan(ant_path,operations_dict,n_jobs,n_machines)
        idx_value.append((idx,makespan))
      
    # take the n smallest makespan
    sorted_values = sorted(idx_value, key=lambda x: x[1])
    ants_idx = sorted_values[:n_operations]

    return [idx for idx,_ in ants_idx]

def stage_2(g,n_jobs,n_machines,nc2,m2,cc2,sequence,operations_dict,stage1_ants):
    # best n paths
    n_operations = 5
    best_paths = best_ants(stage1_ants,n_jobs,n_machines,operations_dict,n_operations)
    
    for _ in range(nc2):
        ants = []

        for _ in range(m2):
            tabu_size = cc2
            sequence_copy = copy.deepcopy(sequence)

            idx_path = random.choice(best_paths)
            tabu = stage1_ants[idx_path]

            sequence_copy = delete_operations(tabu,sequence_copy,n_machines)

            ant = create_path(g,n_machines,sequence_copy,operations_dict,tabu,tabu_size)
            ants.append(ant)
        
        update_evaporating(g)
        update_pheromone(g,ants,operations_dict,n_jobs,n_machines)
    
    return ants

def stage_1(g,n_jobs,n_machines,nc1,m1,cc1,sequence,operations_dict):
    for _ in range(nc1):
        # each ant has a path
        ants = []
        
        for _ in range(m1):
            # visited vertices -> ant path
            tabu = []
            tabu_size = cc1
            
            sequence_copy = copy.deepcopy(sequence)

            # put the ant into a random first feasible vertex
            first_operations = [n_machines*i for i in range(n_jobs)]
            operation = random.choice(first_operations)
            tabu.append(operation)

            # pop in the first used sequence operation
            idx_job = operation // n_machines
            sequence_copy[idx_job].pop(0)
            
            ant = create_path(g,n_machines,sequence_copy,operations_dict,tabu,tabu_size)
            ants.append(ant)
        
        update_evaporating(g)
        update_pheromone(g,ants,operations_dict,n_jobs,n_machines)
    
    return ants

def execute(g,n_jobs,n_machines,sequence,operations_dict):
    # parameters
    nc = 3000 # cycles number
    cc = n_jobs * n_machines # operations number
    m  = cc # ants number
    r  = 0.3 # ratio

    # Stage 1
    m1  = round(r * m)
    nc1 = round(r * nc)
    cc1 = round(r * cc)
    
    stage1_ants = stage_1(g,n_jobs,n_machines,nc1,m1,cc1,sequence,operations_dict)

    # Stage 2
    m2 = m - m1
    nc2 = nc - nc1
    cc2 = cc

    stage2_ants = stage_2(g,n_jobs,n_machines,nc2,m2,cc2,sequence,operations_dict,stage1_ants)
    return stage2_ants

def main():
    file = "datasets//ft06.txt"
    n_jobs, n_machines, operations = read_file(file)

    operations_dict = create_dictionary(operations)
    sequence = create_sequence(n_jobs,n_machines,operations)

    size_graph = n_jobs*n_machines
    g = ig.Graph.Full(n=size_graph, directed=True)
    
    delete_edges(g,n_jobs,n_machines)

    # initial pheromone
    g.es["weight"] = 1

    results = []
    ant_paths = execute(g,n_jobs,n_machines,sequence,operations_dict)

    for ant_path in ant_paths:
        makespan = evaluate_makespan(ant_path,operations_dict,n_jobs,n_machines)
        results.append(makespan)
    
    print(min(results))

main()