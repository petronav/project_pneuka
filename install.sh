PROJ_DIR=$PWD
eval "$(conda shell.bash hook)"
conda create -n pneuka -y python=3.7 && \
conda activate pneuka && \
echo "Conda environment 'pneuka' activated" && \
conda update -n base -c defaults conda

pip install --no-cache-dir \
    kivy==2.0.0 \
    pypdf2==1.26.0 \
    plyer==2.0.0 \
    pdf2image==1.14.0 \
    PyMuPDF==1.18.14 \
    kivy-garden==0.1.4 \
    # opencv-python==4.5.5 \
    opencv-python==4.5.5.62 \
    numpy==1.21.5 \
    plyer==2.1.0 \
    pyobjus==1.2.3