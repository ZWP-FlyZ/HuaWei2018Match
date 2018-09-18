# -*- coding: utf-8 -*-
'''
Created on 2018年9月17日

@author: zwp12
'''

'''
用分支界限法求解 装配问题

'''

import math;
import heapq;
import copy;

CPU_FLAG=0;
MEM_FLAG=1;


class Bbnode():
    parent=None;
    lchild=0;
    def __init__(self,parent,lchild):
        self.parent=parent;
        self.lchild=lchild;
         
class MaxHeapNode():
    up=0;
    lev=0;
    ptr=None;
    cw=None;
    def __init__(self,up,lev,ptr,cw=None):
        self.up=up;
        self.lev=lev;
        self.ptr=ptr;
        self.cw=cw;
    # 构造极大堆  改变符号
    def __gt__(self, other):
        return self.up < other.up
    def __lt__(self, other):
        return self.up > other.up
    def __ge__(self, other):
        return self.up <= other.up
    def __le__(self, other):
        return self.up >= other.up


def addToHeap(heap,bbnode,up,lchild,lev,cw=None):
    node = MaxHeapNode(up,lev,Bbnode(bbnode,lchild),cw=cw);
    heapq.heappush(heap, node);


def branch_bound_mul(wc,wn,c,opt_tag):
    '''
    >多约束条件
    wc.shape=[约束数目，类数量]
    wn.shape=[类数量]
    c.shape=[约束数目]
    opt_tag:优化目标
    '''
    
    # 约束条件个数
    dim = len(wc);
    
    n = len(wc[0]);
    
    r=[0]*n;
    if n>1:
        for i in range(n-2,0,-1):
            r[i]=r[i+1]+wc[opt_tag][i+1]*wn[i+1];
        r[0]=r[1]+wc[opt_tag][1]*wn[1];  
              
    i=0;
    cw = [0]*dim;
    bbnode=None;# 空父节点
    bestw=0;
    bestx=[0]*n;
    heap=[];
    
    
    # 判断各个约束条件是否满足
    def is_ok(cw,wc,i,k,c):
        for j in range(dim):
            if cw[j]+wc[j][i]*k>c[j]:
                return False;
        return True;
        
    while i<n:
        k = wn[i];
        while k>0:   
            if is_ok(cw,wc,i,k,c):
                # 添加左节点
                # 主优化目标
                tmp = cw[opt_tag]+wc[opt_tag][i]*k;
                if tmp>bestw:
                    bestw=tmp;
                    besti=i;
                    bestk=k;
                    bestbb=bbnode;
                tmp = tmp+r[i];
                # 更新cw
                ncw = copy.deepcopy(cw);
                for j in range(dim):
                    ncw[j]=cw[j]+wc[j][i]*k;   
                addToHeap(heap,bbnode,tmp,k,i+1,ncw);
            k-=1;
            
        # 添加右节点
        if bestw<cw[opt_tag]+r[i]:
            addToHeap(heap,bbnode,cw[opt_tag]+r[i],0,i+1,cw);
        
        if len(heap)==0:break;
        
        node =  heapq.heappop(heap);
        i = node.lev;
        bbnode = node.ptr;
        cw = node.cw;
        
    i=besti-1;
    bestx[besti]=bestk;  
    bbnode = bestbb;
    while i>=0 :
        bestx[i]=bbnode.lchild;
        bbnode= bbnode.parent;
        i-=1;
            
    return bestw,bestx;
    


def packing(v_mac_names,pakcing_tab,p_mac,opt_tag='CPU'):
    '''
    pakcing_tab:按照CPU和MEM升序排序，结构[[CPU,MEM,COT],......]
    p_mac:物理机配置[CPU,MEM]
    opt_tag:优化目标，CPU 或者  MEM
    '''
    v_cpu_ned = 0;v_mem_ned=0;
    opt_flag=CPU_FLAG;# 默认CPU 优化
    opt_wc=[[],[]];opt_wn=[];opt_vname=[];
    
    if opt_tag == 'MEM':opt_flag=MEM_FLAG;
    
    for  i in range(len(pakcing_tab)):
        idx = -i-1;
        opt_vname.append(v_mac_names[idx]);
        la = pakcing_tab[idx];
        opt_wc[0].append(la[0]);# 获得虚拟机优化目标列表
        opt_wc[1].append(la[1]);
        opt_wn.append(la[-1]);
        
        # 观察至少需要几台机器的统计
        v_cpu_ned+=la[CPU_FLAG]*la[-1];# 计算所有cpu数
        v_mem_ned+=la[MEM_FLAG]*la[-1];# 计算过所有mem数
    
    la_cpu_r = v_cpu_ned/p_mac[CPU_FLAG];
    la_mem_r = v_mem_ned/p_mac[MEM_FLAG];
    min_pmac = max(math.ceil(la_cpu_r),
                   math.ceil(la_mem_r));
    
    print('need_res:\t',[v_cpu_ned,v_mem_ned]);
    print('p_mac_res:\t',p_mac);
    print('opt_vname:\t',opt_vname);
    print('opt_wc  :\t',opt_wc);
    print('opt_wn  :\t',opt_wn);
    print('min_mac_ra:\t',[la_cpu_r,la_mem_r]);
    print('min_mac_c:\t',min_pmac);
    
    print('--------------------------------------')
    
    
    def reoge(vn,vwc,vwn,mask):
        nvn=[];
        nvwc=[[] for _ in range(len(vwc))];
        nvwn=[];
        res=[]; 
        for i in range(len(mask)):
            if mask[i]>0:
                # 统计结果
                res.append([vn[i],mask[i]]);
            if vwn[i]-mask[i]>0:
                nvn.append(vn[i]);
                for j in range(len(vwc)):
                    nvwc[j].append(vwc[j][i]);
                nvwn.append(vwn[i]-mask[i]);
        return nvn,nvwc,nvwn,res;
     
     
    p_mac_cot=0;# 物理机数量统计
    packing_res=[];
    while len(opt_wn)>0:
        print('\nreap%d'%(p_mac_cot));
        print('opt_vname:\t',opt_vname);
        print('opt_wc  :\t',opt_wc);
        print('opt_wn  :\t',opt_wn); 
        c,x = branch_bound_mul(opt_wc,opt_wn,p_mac,opt_flag);
        print('res_used:\t',c); 
        print('mask    :\t',x); 
        opt_vname,opt_wc,opt_wn,rec = reoge(opt_vname,opt_wc,opt_wn,x);
        packing_res.append(rec);  
        p_mac_cot+=1;
     
    print(p_mac_cot);
    for i in packing_res:
        print(i);
    
    return packing_res;
    
def run():
    
    pakcing_tab=[[1,1,15],
                 [2,2,13],
                 [4,8,14],
                 [8,16,12],
                 [16,16,15]];
    p_mac=[56,128];
    vnames=['fv1','fv4','fv8','fv11','fv13'];
    packing(vnames,pakcing_tab,p_mac,'MEM');
    
    
    pass;
    

if __name__ == '__main__':
    run();
    
    # print(branch_bound([16,8,4,2,1],[15,12,14,13,15],56));
    pass