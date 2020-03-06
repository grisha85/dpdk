
from collections import defaultdict

global_flags = ""

def check_for_manual_deps(targets, splits):
    splits = set(splits)
    return targets.intersection(splits)

def parse_ninja():
    ninja_to_real_targets = dict()
    targets = set()
    last_flag_groups = None
    flag_group_srcs = list()

    with open("ninja") as f: 
        lines = f.readlines() 

    umakefile = ""
    for line in lines:
        try:
            ar = line.split("&&")[1]
            """ gcc-ar csrD lib/librte_kvargs.a 'lib/76b5a35@@rte_kvargs@sta/librte_kvargs_rte_kvargs.c.o' """
            """ lib/76b5a35@@rte_kvargs@sta/librte_kvargs_rte_kvargs.c.o """
            words = ar.strip().split()
            liba = words[2]
            real_objects = []
            for obj in words[3:]:
                if "@@" in obj and "meson" not in obj:
                    real_objects.append(ninja_to_real_targets[obj])
            targets.add(liba)
            if last_flag_groups:
                umake_line = f':foreach {" ".join(flag_group_srcs)} > gcc {last_flag_groups} {global_flags} -I{{dir}} -c {{filename}} -o {{target}} > {{dir}}/{{noext}}.c.o\n'
                umakefile += umake_line
                last_flag_groups = None
                flag_group_srcs = list()
            umake_line = f": {' '.join(real_objects)} > ar csrD {{target}} {{filename}} > {liba}\n"
            umakefile += umake_line
        except IndexError:
            """ [2/1966] cc -Ilib/76b5a35@@rte_eal@sta -Ilib -I../lib -I. -I../ -Iconfig -I../config -Ilib/librte_eal/common/include -I../lib/librte_eal/common/include -I../lib/librte_eal/linux/eal/include -Ilib/librte_eal/common -I../lib/librte_eal/common -Ilib/librte_eal/common/include/arch/x86 -I../lib/librte_eal/common/include/arch/x86 -Ilib/librte_eal -I../lib/librte_eal -Ilib/librte_kvargs -I../lib/librte_kvargs -fdiagnostics-color=always -pipe -D_FILE_OFFSET_BITS=64 -Wall -Winvalid-pch -O3 -include rte_config.h -Wextra -Wcast-qual -Wdeprecated -Wformat-nonliteral -Wformat-security -Wmissing-declarations -Wmissing-prototypes -Wnested-externs -Wold-style-definition -Wpointer-arith -Wsign-compare -Wstrict-prototypes -Wundef -Wwrite-strings -Wno-missing-field-initializers -D_GNU_SOURCE -fPIC -march=native -mno-avx512f -Wno-format-truncation -DRTE_LIBEAL_USE_GETENTROPY -DALLOW_EXPERIMENTAL_API -MD -MQ 'lib/76b5a35@@rte_eal@sta/librte_eal_common_eal_common_class.c.o' -MF 'lib/76b5a35@@rte_eal@sta/librte_eal_common_eal_common_class.c.o.d' -o 'lib/76b5a35@@rte_eal@sta/librte_eal_common_eal_common_class.c.o' -c ../lib/librte_eal/common/eal_common_class.c """
            ccline = line.strip().split()
            includes = []
            src = ""
            flags = []
            o_index = -1
            if ccline[1] == "cc":
                creating_obj = False
                for idx, ccword in enumerate(ccline[2:]):
                    if "@@" in ccword:
                        pass
                    elif ccword.startswith("-I"):
                        if "@@" in ccword:
                            # print(ccword)
                            # to_replace = find_between(ccword, "/", "@")
                            # ninja = ccword.replace(to_replace, "/lib")
                            # ninja = ninja.replace("@sta","")
                            # print(ninja)
                            # includes.append(ninja)
                            continue
                        elif ccword.startswith("-I../"):
                            includes.append(ccword.replace("-I../", "-I./"))
                        else:
                            includes.append(ccword.replace("-I", "-Ibuild/"))
                    elif "-c" == ccword:
                        creating_obj = True
                        if not ccline[-1].startswith("../"):
                            continue
                        src = ccline[-1][3:]
                        ninja_target = ccline[-3]
                        if "meson" in ninja_target:
                            continue
                        if ninja_target in ninja_to_real_targets:
                            raise ValueError(f"target already exists {ninja_target}")
                        ninja_to_real_targets[ninja_target] = f"{src}.o"
                    elif "-o" == ccword:
                        o_index = idx
                    elif idx == o_index + 1:
                        pass
                    else:
                        if ccword.startswith("-M") or ".c.o" in ccword or "@@" in ccword:
                            continue
                        else:
                            if "-pipe" not in ccword:
                                flags.append(ccword)
                if creating_obj:
                    if not src:
                        continue
                    flags = flags[:-1]
                    targets.add(f"{src}.o")
                    manual_deps = check_for_manual_deps(targets, ccline)
                    flag_group = f'{" ".join(includes)} {" ".join(flags)}'
                    if last_flag_groups == flag_group:
                        flag_group_srcs.append(src)
                    else:
                        if last_flag_groups:
                            umake_line = f':foreach {" ".join(flag_group_srcs)} > gcc {last_flag_groups} {global_flags} -I{{dir}} -c {{filename}} -o {{target}} > {{dir}}/{{noext}}.c.o\n'
                            umakefile += umake_line
                            last_flag_groups = None
                            flag_group_srcs = list()
                        
                        last_flag_groups = flag_group
                        flag_group_srcs.append(src)

                else:
                    if last_flag_groups:
                        umake_line = f':foreach {" ".join(flag_group_srcs)} > gcc {last_flag_groups} {global_flags} -I{{dir}} -c {{filename}} -o {{target}} > {{dir}}/{{noext}}.c.o\n'
                        umakefile += umake_line
                        last_flag_groups = None
                        flag_group_srcs = list()
                
                    flags = flags[2:]
                    target = ccline[3]
                    srcs = []
                    for idx, ccword in enumerate(ccline[2:]):
                        if "@@" in ccword and "meson" not in ccword:
                            srcs.append(ninja_to_real_targets[ccword])
                    targets.add(f"{target}")
                    manual_deps = check_for_manual_deps(targets, ccline)
                    manual_deps.remove(target)
                    umake_line = f': {" ".join(srcs)} | {" ".join(manual_deps)} > gcc {{filename}} {" ".join(includes)} {" ".join(flags)} {global_flags} -o {{target}} > {target}\n'
                    umakefile += umake_line
    return umakefile


umakefile = parse_ninja()
with open("UMakefile", "w") as f:
    f.write(umakefile)


    