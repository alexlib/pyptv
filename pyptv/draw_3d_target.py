# How to run:
# python .\draw_3d_target.py .\cal\pyramide_target.txt


import numpy as np
import matplotlib.pyplot as plt
# %matplotlib tk

# %%
# filename = '../cal/small_target_cam2.txt'
def plot_3d_target(filename):
    d = np.loadtxt(filename)

    # %%
    from mpl_toolkits.mplot3d import Axes3D
    ax = plt.figure(figsize=(12,10)).add_subplot(projection='3d')

    # 
    for row in d:
        ax.plot(row[1],row[2],row[3],'ro')
        ax.text(row[1],row[2],row[3],f'{row[0]:.0f}',None)

    ax.set_xlim(d[:,1].min(),d[:,1].max())
    ax.set_ylim(d[:,2].min(),d[:,2].max())
    ax.set_zlim(d[:,3].min(),d[:,3].max())

    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    ax.set_title(filename.split('/')[-1])

    plt.show()

if __name__ == "__main__":
    import sys
    plot_3d_target(sys.argv[1])


