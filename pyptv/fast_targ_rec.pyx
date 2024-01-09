# fast_targ_rec.pyx
from typing import List
from openptv_python.constants import MAX_TARGETS, CORRES_NONE

def fast_targ_rec(img, int thres, int disco, int nnmin, int nnmax,
                  int nxmin, int nxmax, int nymin, int nymax,
                  int sumg_min, int xmin, int xmax, int ymin, int ymax) -> List:
    cdef int n = 0
    cdef int n_wait = 0
    cdef int n_targets = 0
    cdef int sumg = 0
    cdef int numpix = 0

    img0 = [row[:] for row in img]  # Make a deep copy of the original image

    waitlist = [[0] * 2 for _ in range(MAX_TARGETS)]

    xa = 0
    ya = 0
    xb = 0
    yb = 0
    x4 = [0] * 4
    y4 = [0] * 4

    pix = []

    for i in range(ymin, ymax):
        for j in range(xmin, xmax):
            gv = img0[i][j]
            if gv > thres:
                if (
                    (gv >= img0[i][j - 1]) and (gv >= img0[i][j + 1]) and
                    (gv >= img0[i - 1][j]) and (gv >= img0[i + 1][j]) and
                    (gv >= img0[i - 1][j - 1]) and (gv >= img0[i + 1][j - 1]) and
                    (gv >= img0[i - 1][j + 1]) and (gv >= img0[i + 1][j + 1])
                ):
                    yn = i
                    xn = j

                    sumg = int(gv)
                    img0[i][j] = 0

                    xa = xn
                    xb = xn
                    ya = yn
                    yb = yn

                    gv -= thres
                    x = xn * gv
                    y = yn * gv
                    numpix = 1
                    waitlist[0][0] = j
                    waitlist[0][1] = i
                    n_wait = 1

                    while n_wait > 0:
                        gvref = img[waitlist[0][1]][waitlist[0][0]]

                        x4[0] = waitlist[0][0] - 1
                        y4[0] = waitlist[0][1]
                        x4[1] = waitlist[0][0] + 1
                        y4[1] = waitlist[0][1]
                        x4[2] = waitlist[0][0]
                        y4[2] = waitlist[0][1] - 1
                        x4[3] = waitlist[0][0]
                        y4[3] = waitlist[0][1] + 1

                        for n in range(4):
                            xn = x4[n]
                            yn = y4[n]
                            if xn >= xmax or yn >= ymax or xn < 0 or yn < 0:
                                continue

                            gv = img0[yn][xn]

                            if (
                                (gv > thres) and (xn > xmin - 1) and (xn < xmax + 1) and
                                (yn > ymin - 1) and (yn < ymax + 1) and
                                (gv <= gvref + disco) and (gvref + disco >= img[yn - 1][xn]) and
                                (gvref + disco >= img[yn + 1][xn]) and (gvref + disco >= img[yn][xn - 1]) and
                                (gvref + disco >= img[yn][xn + 1])
                            ):
                                sumg += gv
                                img0[yn][xn] = 0
                                if xn < xa:
                                    xa = xn
                                if xn > xb:
                                    xb = xn
                                if yn < ya:
                                    ya = yn
                                if yn > yb:
                                    yb = yn
                                waitlist[n_wait][0] = xn
                                waitlist[n_wait][1] = yn

                                x += xn * (gv - thres)
                                y += yn * (gv - thres)

                                numpix += 1
                                n_wait += 1

                        n_wait -= 1
                        for m in range(n_wait):
                            waitlist[m][0] = waitlist[m + 1][0]
                            waitlist[m][1] = waitlist[m + 1][1]
                        waitlist[n_wait][0] = 0
                        waitlist[n_wait][1] = 0

                    if (
                        xa == (xmin - 1) or ya == (ymin - 1) or
                        xb == (xmax + 1) or yb == (ymax + 1)
                    ):
                        continue

                    nx = xb - xa + 1
                    ny = yb - ya + 1

                    if (
                        numpix >= nnmin and numpix <= nnmax and
                        nx >= nxmin and nx <= nxmax and
                        ny >= nymin and ny <= nymax and sumg > sumg_min
                    ):
                        sumg -= numpix * thres
                        x /= sumg
                        x += 0.5
                        y /= sumg
                        y += 0.5
                        pix.append([x, y, CORRES_NONE, n_targets, numpix, nx, ny, sumg])
                        n_targets += 1
                        xn = x
                        yn = y

    return pix
