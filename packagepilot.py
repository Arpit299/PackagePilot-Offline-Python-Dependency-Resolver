import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
VERSION_RE=re.compile(r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:-([0-9A-Za-z.-]+))?$')
REQ_RE=re.compile(r'^([A-Za-z0-9_.-]+)\s*(.*)$')
CONSTRAINT_RE=re.compile(r'^(==|!=|>=|<=|>|<|~=|\^|=)?\s*([0-9A-Za-z.*+!-]+)$')
@dataclass(frozen=True,order=True)
class Version:
    major:int
    minor:int
    patch:int
    prerelease:str=''
    @staticmethod
    def parse(value):
        match=VERSION_RE.fullmatch(str(value).strip())
        if not match:
            raise ValueError(f'invalid version: {value}')
        return Version(int(match.group(1)),int(match.group(2) or 0),int(match.group(3) or 0),match.group(4) or '')
    def base(self):
        return (self.major,self.minor,self.patch)
    def __str__(self):
        return f'{self.major}.{self.minor}.{self.patch}'+(f'-{self.prerelease}' if self.prerelease else '')
class Constraint:
    def __init__(self,operator='',value=None):
        self.operator=operator or ''
        self.value=Version.parse(value) if value else None
    def matches(self,version):
        if not self.operator:
            return True
        v=version.base()
        t=self.value.base()
        if self.operator in ('=','=='):
            return v==t
        if self.operator=='!=':
            return v!=t
        if self.operator=='>=':
            return v>=t
        if self.operator=='<=':
            return v<=t
        if self.operator=='>':
            return v>t
        if self.operator=='<':
            return v<t
        if self.operator=='~=':
            upper=(self.value.major+1,0,0) if self.value.major else (0,self.value.minor+1,0)
            return v>=t and v<upper
        if self.operator=='^':
            if self.value.major:
                upper=(self.value.major+1,0,0)
            elif self.value.minor:
                upper=(0,self.value.minor+1,0)
            else:
                upper=(0,0,self.value.patch+1)
            return v>=t and v<upper
        return False
    def __str__(self):
        return f'{self.operator}{self.value}' if self.operator else '*'
class PackageSpec:
    def __init__(self,name,constraints=None):
        self.name=name
        self.constraints=tuple(constraints or ())
    @staticmethod
    def parse(value):
        text=str(value).strip()
        match=REQ_RE.fullmatch(text)
        if not match:
            raise ValueError(f'invalid requirement: {value}')
        name=match.group(1)
        tail=match.group(2).strip()
        if not tail:
            return PackageSpec(name)
        constraints=[]
        for token in tail.split(','):
            part=token.strip()
            cmatch=CONSTRAINT_RE.fullmatch(part)
            if not cmatch:
                raise ValueError(f'invalid constraint: {part}')
            constraints.append(Constraint(cmatch.group(1) or '',cmatch.group(2)))
        return PackageSpec(name,constraints)
    def __str__(self):
        return self.name+(''.join(str(item) for item in self.constraints))
class PackageIndex:
    def __init__(self,data):
        self.packages={}
        for name,versions in data.items():
            entries=[]
            for version,dependencies in versions.items():
                entries.append((Version.parse(version),[PackageSpec.parse(dep) for dep in dependencies]))
            entries.sort(key=lambda item:item[0],reverse=True)
            self.packages[name]=entries
    @staticmethod
    def from_file(path):
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        return PackageIndex(data.get('packages',data))
    def available(self,name):
        return self.packages.get(name,[])
class ResolutionError(Exception):
    pass
class Resolver:
    def __init__(self,index,installed=None):
        self.index=index
        self.installed={name:Version.parse(version) for name,version in (installed or {}).items()}
        self.constraints=defaultdict(list)
        self.assignments={}
        self.explored=0
    def add_root(self,spec):
        self.constraints[spec.name].extend(spec.constraints)
    def candidates(self,name):
        constraints=self.constraints[name]
        result=[]
        for version,deps in self.index.available(name):
            if all(constraint.matches(version) for constraint in constraints):
                result.append((version,deps))
        if name in self.installed:
            current=self.installed[name]
            result.sort(key=lambda item:(item[0].base()==current.base(),item[0]),reverse=True)
        return result
    def choose_unresolved(self):
        names=[name for name in self.constraints if name not in self.assignments]
        if not names:
            return None
        scored=[(len(self.candidates(name)),name) for name in names]
        scored.sort(key=lambda item:(item[0],item[1]))
        return scored[0][1]
    def solve(self):
        if not self.constraints:
            raise ResolutionError('no requirements provided')
        self.explored=0
        if not self._search():
            details=[]
            for name in sorted(self.constraints):
                candidates=self.candidates(name)
                if not candidates:
                    details.append(f'{name}: '+','.join(str(c) for c in self.constraints[name]))
            suffix=f' | conflicts: {"; ".join(details)}' if details else ''
            raise ResolutionError('no compatible resolution found'+suffix)
        return dict(sorted(self.assignments.items()))
    def _search(self):
        self.explored+=1
        name=self.choose_unresolved()
        if name is None:
            return self._validate_all()
        candidates=self.candidates(name)
        if not candidates:
            return False
        for version,deps in candidates:
            self.assignments[name]=version
            added=[]
            valid=True
            for dep in sorted(deps,key=lambda item:item.name):
                self.constraints[dep.name].extend(dep.constraints)
                added.append(dep)
                if dep.name not in self.index.packages:
                    valid=False
                    break
                if dep.name in self.assignments and not all(constraint.matches(self.assignments[dep.name]) for constraint in self.constraints[dep.name]):
                    valid=False
                    break
            if valid and self._search():
                return True
            self.assignments.pop(name,None)
            for dep in reversed(added):
                for _ in dep.constraints:
                    self.constraints[dep.name].pop()
                if not self.constraints[dep.name]:
                    del self.constraints[dep.name]
        return False
    def _validate_all(self):
        return all(all(constraint.matches(version) for constraint in self.constraints[name]) for name,version in self.assignments.items())
    def graph(self):
        graph={}
        for name,version in self.assignments.items():
            deps=[]
            for candidate_version,requirements in self.index.available(name):
                if candidate_version==version:
                    deps=sorted(spec.name for spec in requirements)
                    break
            graph[name]=deps
        return dict(sorted(graph.items()))
    def plan(self):
        actions=[]
        for name,version in self.assignments.items():
            if name not in self.installed:
                actions.append(('INSTALL',name,version,None))
            elif self.installed[name].base()!=version.base():
                kind='DOWNGRADE' if version<self.installed[name] else 'UPGRADE'
                actions.append((kind,name,version,self.installed[name]))
            else:
                actions.append(('KEEP',name,version,None))
        for name,version in self.installed.items():
            if name not in self.assignments:
                actions.append(('REMOVE',name,version,None))
        order={'REMOVE':0,'DOWNGRADE':1,'UPGRADE':2,'INSTALL':3,'KEEP':4}
        actions.sort(key=lambda item:(order[item[0]],item[1]))
        return actions
def parse_installed(path):
    if not path:
        return {}
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    return data.get('installed',data)
def read_requirements(path):
    items=[]
    for raw in Path(path).read_text(encoding='utf-8').splitlines():
        text=raw.strip()
        if text and not text.startswith('#'):
            items.append(PackageSpec.parse(text))
    return items
def build_index_demo():
    return PackageIndex({'alpha':{'1.0.0':['beta>=1.0,<2.0','gamma>=1.0,<3.0'],'2.0.0':['beta>=2.0,<3.0','gamma>=2.0,<3.0']},'beta':{'1.0.0':[],'1.5.0':[],'2.0.0':['delta>=1.0,<2.0'],'2.5.0':['delta>=2.0,<3.0']},'gamma':{'1.0.0':[],'2.0.0':['delta>=1.0,<2.0'],'2.5.0':['delta>=2.0,<3.0']},'delta':{'1.0.0':[],'1.5.0':[],'2.0.0':[]}})
def run_demo(verbose=True):
    index=build_index_demo()
    resolver=Resolver(index,{'beta':'1.5.0'})
    resolver.add_root(PackageSpec.parse('alpha>=1.0,<2.0'))
    result=resolver.solve()
    expected={'alpha':Version.parse('1.0.0'),'beta':Version.parse('1.5.0'),'delta':Version.parse('2.0.0'),'gamma':Version.parse('2.5.0')}
    if result!=expected:
        raise AssertionError(f'unexpected resolution: {result}')
    plan=resolver.plan()
    if not any(item[0]=='KEEP' and item[1]=='beta' for item in plan):
        raise AssertionError('safe update plan failed')
    graph=resolver.graph()
    if graph['alpha']!=['beta','gamma'] or graph['beta']!=[] or graph['gamma']!=['delta']:
        raise AssertionError('dependency graph mismatch')
    conflict=Resolver(index)
    conflict.add_root(PackageSpec.parse('beta>=1.0,<2.0'))
    conflict.add_root(PackageSpec.parse('beta>=2.0,<3.0'))
    failed=False
    try:
        conflict.solve()
    except ResolutionError:
        failed=True
    if not failed:
        raise AssertionError('conflict detection failed')
    if verbose:
        print('PACKAGEPILOT SELF-TEST: PASS')
        print('Resolved: '+', '.join(f'{name}=={version}' for name,version in result.items()))
        print('Search States: '+str(resolver.explored))
        print('Dependency Graph:')
        for name,deps in graph.items():
            print(f'  {name}: '+(', '.join(deps) if deps else '-'))
        print('Plan:')
        for action,name,version,old in plan:
            suffix=f' from {old}' if old else ''
            print(f'  {action} {name}=={version}{suffix}')
    return result
def run_resolve(index_path,requirements_path,installed_path=None,output_path=None):
    index=PackageIndex.from_file(index_path)
    resolver=Resolver(index,parse_installed(installed_path))
    requirements=read_requirements(requirements_path)
    for spec in requirements:
        resolver.add_root(spec)
    result=resolver.solve()
    payload={'requirements':[str(item) for item in requirements],'resolved':{name:str(version) for name,version in result.items()},'search_states':resolver.explored,'graph':resolver.graph(),'plan':[{'action':action,'package':name,'version':str(version),'previous':str(old) if old else None} for action,name,version,old in resolver.plan()]}
    if output_path:
        Path(output_path).write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(json.dumps(payload,indent=2))
def main():
    parser=argparse.ArgumentParser(prog='packagepilot')
    parser.add_argument('command',nargs='?',choices=['self-test','demo','resolve'])
    parser.add_argument('index',nargs='?')
    parser.add_argument('requirements',nargs='?')
    parser.add_argument('--installed')
    parser.add_argument('--output')
    parser.add_argument('--self-test',action='store_true',dest='self_test')
    args=parser.parse_args()
    if args.self_test or not args.command:
        run_demo()
        return 0
    if args.command=='demo':
        run_demo()
        return 0
    if args.command=='resolve':
        if not args.index or not args.requirements:
            parser.error('resolve requires index and requirements files')
        run_resolve(args.index,args.requirements,args.installed,args.output)
        return 0
    return 0
if __name__=='__main__':
    sys.exit(main())
