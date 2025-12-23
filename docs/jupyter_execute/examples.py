#!/usr/bin/env python
# coding: utf-8

# In[1]:


import stashmap
sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)


# In[2]:


stashmap.describe_variable("m01s01i004")


# In[3]:


sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)

stashmap.describe_variable(sections)

variables = [s for s in sections if isinstance(s, stashmap.Variable)]

for v in variables[0:15]:
    print("isec=", v.record.get('isec'), "item=", v.record.get('item'), "->", v.record.get('description'))


# In[4]:


sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)

stashmap.describe_profiles(sections)

time = [s for s in sections if isinstance(s, stashmap.TimeProfile)]

for t in time:
    print(t.record.get('tim_name'), "->", t.record.get('description'))


# In[5]:


sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)

stashmap.describe_profiles(sections)

domain = [s for s in sections if isinstance(s, stashmap.DomainProfile)]

for d in domain:
    print(d.record.get('dom_name'), "->", d.record.get('description'))


# In[6]:


stashmap.export_sections_to_csv(sections, "examples/stash")


# In[7]:


stashmap.write_namelist(sections, "examples/new_stash.txt")

N = 10
with open("examples/new_stash.txt", "r") as file:
    for i in range(N):
        line = next(file).strip()
        print(line)


# In[8]:


stashmap.write_namelist("examples/stash_variables.csv", "examples/new_stash.txt")

N = 10
with open("examples/new_stash.txt", "r") as file:
    for i in range(N):
        line = next(file).strip()
        print(line)

