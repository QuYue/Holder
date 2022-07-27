#%%
class Holder():
    def __init__(self, data=[]):
        self.data = data
        self.max_show = 5

    @property
    def shape(self):
        def count(a):
            dim = []
            if isinstance(a, list):
                dim.append(len(a))
                if len(a) > 0:
                    dim += count(a[0])
            return dim
        dim = count(self.data)
        return tuple(dim)

    @property
    def dim(self):
        return len(self.shape)

    def tolist(self):
        return self.data

    def __len__(self):
        return len(self.data)

    def __get_slice(self, n, a):
        if isinstance(n,int):
            return a[n]
        elif isinstance(n,list):
            L = []
            for i in n:
                if isinstance(i,int): L.append(a[i])
            return L
        elif isinstance(n,slice):
            return a[n]
        else:
            assert False, f"Holder indices must be integers or list or slices, not {type(n)}."

    def __select(self, data, inputs, dim=0):
            data = self.__get_slice(inputs[0], data)
            if len(inputs) != 1 :
                if isinstance(inputs[0],int):
                    L = self.__select(data, inputs[1:],dim+1)
                else:
                    L = []
                    for d in data:
                        L.append(self.__select(d, inputs[1:],dim+1))
                data = L
            return data

    def __getitem__(self, *inputs):
        if isinstance(inputs[0], tuple):
            inputs = inputs[0]
        assert self.dim >= len(inputs), f"The shape of Holder is {self.shape}, but your indices is {inputs}, of which dimension is larger."
        data = self.__select(self.data, inputs)
        if isinstance(data,list):
                return Holder(data)
        else:
            return data

    def __select2(self, command, k, v, dim=0):
        if len(k) == 0:
            exec(command+'=v')  
            return None
        if isinstance(k[0], int):
            self.__select2(command+f'[{k[0]}]', k[1:], v, dim)
        # elif isinstance(k[0], slice):
        #     p = lambda x: '' if x is None else x
        #     c = f"[{p(k[0].start)}:{p(k[0].stop)}:{p(k[0].step)}]"
        #     self.__select2(command+c, k[1:], v, dim+1)
        elif isinstance(k[0], list):
            a = 'v'
            for i in range(dim):
                a+='[:]'
            for j,i in enumerate(k[0]):
                self.__select2(command+f'[{i}]', k[1:], eval(a+f'[{j}]'), dim)
    
    def __setitem__(self, k, v):
        shape1 = self.shape
        if not isinstance(k, tuple):
            k = [k]
        assert self.dim >= len(k), f"The shape of Holder is {shape1}, but your indices is {k}, of which dimension is larger."
        if len(k) == self.dim:
            check = True
            for i in range(len(k)):
                if not isinstance(k[i],int): 
                    check = False
                    break
            if check:
                if isinstance(v, Holder):
                    assert v.dim==0,  f"The shape of Split Holder is {tuple()}, but the shape of data is {v.shape}, of which dimension is larger."
                else:
                    v = Holder(v)
        shape = []
        for i in shape1:
            shape.append(list(range(i)))
        for i,index in enumerate(k):
            shape[i] = self.__get_slice(index, shape[i])
        new_shape = [len(i) for i in shape if isinstance(i,list) and len(i)>0]
        if isinstance(v, list):
            v = Holder(v)
        try:
            shape2 = v.shape
        except:
            assert False, "Holder can only be assigned to a data with 'shape' attribute."
        check = True
        if len(new_shape) == len(shape2):
            for i,j in zip(new_shape, shape2):
                if i!=j: check=False
        else:
            check = False
        assert check, f"The shape of the sliced Holder is {tuple(new_shape)}, but the shape of input data is {shape2}."
        command = 'self.data'
        v = v.tolist()
        self.__select2(command, shape, v)

    def append(self, new_Holder, dim=0):
        def app(a, b, n=0):
            if n==dim:
                return a + b
            else:
                L = []
                for i in range(len(a)):
                    L.append(app(a[i], b[i], n+1))
                return L
        assert isinstance(new_Holder, Holder) or isinstance(new_Holder, list), f"The first input of Function 'append' must be a Holder or a List, not {type(new_Holder)}."
        shape1 = self.shape
        if isinstance(new_Holder, list):
            new_Holder = Holder(new_Holder)
        shape2 = new_Holder.shape
        assert self.dim == new_Holder.dim, f"The shape of Holder is {shape1}, but the shape of new Holder, which need to be append, is {shape2}, can not be concatenated."
        assert self.dim > dim, f"The second input of Function 'append' is dimension for concatenation, the shape of Holders are {shape1} and {shape2}, but dimension input by your is {dim}."
        check = True
        for i in range(len(shape1)):
            if i != dim and shape1[i]!=shape2[i]:
                check = False
        assert check,  f"Can not concatenate. Because the shape of Holders are {shape1} and {shape2}, the dimension for concatenation is {dim}."
        data = app(self.data, new_Holder.data)
        return Holder(data)
    
    def concat(self, Holder_list, dim=0):
        assert isinstance(Holder_list, list), f"The first input of Function 'concat' must be a List, not {type(Holder_list)}."
        d = self
        for i in Holder_list:
            d = d.append(i, dim)
        return d
        
    def pprint(self, data, max_dim=1, dim=0):
        p = ''
        bigger = False
        if len(data)>self.max_show+1:
            data = data[:self.max_show]+data[-1:]
            bigger = True
        length = len(data)
        if dim < max_dim-1:
            for i in range(length):
                if i==length-1 and bigger:
                    p += f"{' '*(dim+1)}...\n"
                if i != 0:
                    p += f"{' '*(dim+1)}"
                p += '['
                p += self.pprint(data[i], max_dim, dim+1)
                p += '],\n'
        else:
            for i in range(length):
                if i==length-1 and bigger:
                    p=p[:-1]
                    p+='...,'
                p += f"{data[i]}, "
        p = p[:-2]
        return p

    def new_axis(self, dim):
        def add_axis(data, dim=0, new_dim=0):
            if dim == new_dim:
                data = [data]
            else:
                L = []
                for i in data:
                    L.append(add_axis(i, dim+1, new_dim))
                data = L
            return data
        assert isinstance(dim, int) and 0<=dim<=self.dim, f"The dimension of Holder is {self.dim}, but the new axis input by you is {dim}, which is bigger."
        data = add_axis(self.data,0,dim)
        return Holder(data)
        
    def __repr__(self):
        p = f"{self.__class__.__name__} with shape {self.shape}\n"
        p += '['
        p += self.pprint(self.data, max_dim=self.dim, dim=0, )
        p += ']'
        return p

        


import numpy as np
a = np.ones([10,4,5,2]).tolist()
a = Holder(a)
a[0,:,0,:] = np.ones([4,2])*2
d = a[0,:,0,:]



#%%
