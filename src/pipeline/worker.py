import sys,json,os,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from geo import evaluate
pcd,tls_npy,vox=sys.argv[1],sys.argv[2],float(sys.argv[3])
tls=np.load(tls_npy)
print("@@JSON@@"+json.dumps(evaluate(pcd,tls,voxel=vox)))
