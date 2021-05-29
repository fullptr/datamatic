"""
A tool for generating code based on a schema of components.
"""
from datamatic import main

if __name__ == "__main__":
    args = main.parse_args()
    main.main(args)