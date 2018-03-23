import dialogue as d

if __name__ == '__main__':
    # Stuff in GoMLQ.sh
    r1 = d.create_run_dict('LOADLEVEL', 'RC3', 'Run 1', 'jdk1.8-u121', 30, 600,
                    '"-Xms29g -Xmx29g -Xmn27g -XX:ParallelGCThreads=48"', 4,
                    'NONE', 154, 45, 23)
    r2 = d.create_run_dict('PRESET', 'RC3', 'Run 2', 'jdk1.8-u121', 80000, 400,
    '"-Xms29g -Xmx29g -Xmn27g -XX:+UseCompressedOops -XX:ParallelGCThreads=48"',
    2, 'NONE', 154, 45, 23 )
    r3 = d.create_run_dict('HBIR_RT', 'RC3', 'Run 3', 'jdk1.8-u121', 0, 
    '"-Xms29g -Xmx29g -Xmn27g -XX:+UseCompressedOops -XX:ParallelGCThreads=48"',
    2, 'NONE', 154, 45, 23)

    print("Testing good runs... " +
        ("passed" if all(d.execute_runs([r1, r2, r3])) else "failed"))

    print("Testing a silly run... " +
        ("passed" if not d.execute_run(d.create_run_dict('FOO')) else "failed"))
