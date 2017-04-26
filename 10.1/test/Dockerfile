# Extending the image using s2i concept can be done with a new Dockerfile as well
# This way we can for example install additional RPM packages
FROM __IMAGE_NAME__
USER 0
RUN INSTALL_PKGS="openssh-server" && \
    yum install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    rpm -V $INSTALL_PKGS && \
    yum clean all
USER 27
COPY test-app /opt/app-root/src

