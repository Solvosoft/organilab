import JsBarcode from 'JsBarcode';

document.getElementById('id_barcode').addEventListener('change', (event) => {
    event.target.value;
    const barcodesvg = document.createElement("svg");
    barcodesvg.className = "barcode";
    document.body.insert(barcodesvg);
    barcodesvg.id=svgCanvas.getNextId();
    JsBarcode(barcodesvg.id, document.getElementById('id_barcode').value);
});
