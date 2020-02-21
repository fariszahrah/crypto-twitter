import sys
import collect
import cluster
import classify


def main():
    with open('./summary.txt','w') as f:
        sys.stdout = f
        collect.main()      
        cluster.main()
        classify.main()
    



if __name__ == "__main__":
    main()
