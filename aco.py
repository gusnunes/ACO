import igraph as ig

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

def create_edges(g,n_jobs,n_machines):
    inicio = 0
    fim = n_machines
    
    for _ in range(n_jobs):
        edges = [(x,x+1) for x in range(inicio,fim-1)]
        g.add_edges(edges)

        inicio = fim
        fim += n_machines

        print(edges) 

def create_label(g):
    n_vertices = g.vcount()
    label = [i for i in range(1,n_vertices+1)]
    g.vs["label"] = label

def main():
    file = "datasets//teste.txt"
    n_jobs, n_machines, operations = read_file(file)

    g = ig.Graph()
    # g.add_vertices(n_jobs*n_machines)

    # create_edges(g,n_jobs,n_machines)
    # create_label(g)

    g = ig.Graph.Full(n=n_jobs*n_machines)
    create_label(g)

    layout = g.layout("kk")
    ig.plot(g, layout=layout, bbox=(800, 800))


main()