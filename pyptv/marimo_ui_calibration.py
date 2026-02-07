import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium", auto_download=["ipynb"])


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from wigglystuff import ChartPuck

    return ChartPuck, mo, np, plt


@app.cell
def _():
    from imageio.v3 import imread

    image = imread("tests/test_cavity/cal/cam1.tif")
    return (image,)


@app.cell
def _(ChartPuck, image, np, plt):
    x_multi = np.random.randn(50)
    y_multi = np.random.randn(50)

    fig, ax = plt.subplots(figsize=(12, 12))
    # ax2.scatter(x_multi, y_multi, alpha=0.6)
    ax.imshow(image, cmap="gray")
    # ax2.set_xlim(-3, 3)
    # ax2.set_ylim(-3, 3)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Drag any puck - closest one will move")
    ax.grid(True, alpha=0.3)

    multi_puck = ChartPuck(
        fig,
        x=[
            image.shape[0] / 2 - 50,
            image.shape[0] / 2 - 15,
            image.shape[0] / 2 + 15,
            image.shape[0] / 2 + 50,
        ],
        y=[
            image.shape[1] / 2,
            image.shape[1] / 2,
            image.shape[1] / 2,
            image.shape[1] / 2,
        ],
        puck_color="#2196f3",
        puck_radius=11,
        puck_alpha=0.2,
    )
    plt.close(fig)
    return (multi_puck,)


@app.cell
def _(mo, multi_puck):
    multi_widget = mo.ui.anywidget(multi_puck)
    return (multi_widget,)


@app.cell
def _(multi_widget):
    multi_widget
    return


@app.cell
def _(mo, multi_widget):
    positions = [
        f"Puck {i + 1}: ({x:.2f}, {y:.2f})"
        for i, (x, y) in enumerate(zip(multi_widget.x, multi_widget.y))
    ]
    mo.callout("\n".join(positions))
    return


if __name__ == "__main__":
    app.run()
