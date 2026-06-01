(() => {
    const modalElement = document.getElementById("globalConfirmModal");
    if (typeof bootstrap === "undefined") {
        return;
    }

    if (modalElement) {
        const modalTitle = document.getElementById("globalConfirmModalTitle");
        const modalText = document.getElementById("globalConfirmModalText");
        const confirmButton = document.getElementById("globalConfirmModalButton");
        const modal = new bootstrap.Modal(modalElement);
        let pendingForm = null;

        document.addEventListener("click", (event) => {
            const trigger = event.target.closest("[data-confirm-submit]");
            if (!trigger) {
                return;
            }

            event.preventDefault();
            const targetSelector = trigger.getAttribute("data-confirm-target");
            if (!targetSelector) {
                return;
            }

            const form = document.querySelector(targetSelector);
            if (!form) {
                return;
            }

            pendingForm = form;
            if (modalTitle) {
                modalTitle.textContent = trigger.getAttribute("data-confirm-title") || "Please confirm";
            }
            if (modalText) {
                modalText.textContent =
                    trigger.getAttribute("data-confirm-message") ||
                    "This action cannot be undone. Do you want to continue?";
            }
            modal.show();
        });

        if (confirmButton) {
            confirmButton.addEventListener("click", () => {
                if (!pendingForm) {
                    return;
                }

                pendingForm.submit();
                pendingForm = null;
            });
        }
    }

    const uploadModal = document.getElementById("uploadCsvModal");
    if (!uploadModal) {
        return;
    }

    uploadModal.addEventListener("hidden.bs.modal", () => {
        const uploadForm = uploadModal.querySelector("form");
        if (uploadForm) {
            uploadForm.reset();
        }
    });
})();
