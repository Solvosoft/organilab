"use strict";
if (!String.prototype.startsWith) {
    String.prototype.startsWith = function (a, b) {
        return this.substr(b || 0, a.length) === a;
    };
}
var FvaClienteInterno = function (laConfiguracion) {
    this.AsigneElTextoALaVentana = AsigneElTextoALaVentana;
    this.MuestreLaVentanaModal = MuestreLaVentanaModal;
    this.OculteLaVentanaModal = OculteLaVentanaModal;
    this.MuestreElBotonDeAceptar = MuestreElBotonDeAceptar;
    this.OculteElBotonDeAceptar = OculteElBotonDeAceptar;
    this.MuestreLaAnimacionDeEspera = MuestreLaAnimacionDeEspera;
    this.OculteLaAnimacionDeEspera = OculteLaAnimacionDeEspera;
    this.MuestreElBordeDeError = MuestreElBordeDeError;
    this.RemuevaElBordeDeError = RemuevaElBordeDeError;
    this.EnvieLaSolicitud = EnvieLaSolicitud;
    var elBotonDeAceptar = $("<div>", { class: "fvaBoton" }).html("Aceptar");
    var elFondoOscuro = $("<div>", { class: "fvaFondoOscuro" });
    var laVentanaModal = $("<div>", { class: "fvaVentanaModal" }).css({ display: "none" });
    var elContenidoDelCuerpo = $("<div>", { class: "fvaContenidoVentanaModal" });
    var elContenidoDeTexto = $("<div>", { class: "fvaMargenDeContenido" });
    var elContenidoDeCopieCodigo = $("<div>", { class: "fvaContenidoDeCopieCodigo" });
    var elAcordeon = $("<div>", { class: "fvaAcordeon" });
    var elPanelAcordeon = $("<div>", { class: "fvaPanelAcordeon" });
    var elToolTipText = $("<span>", { class: "fvaToolTipText" });
    var elCodigoConBotonCopiar = $("<div>", { class: "fvaCodigoConBotonCopiar" });
    var laAnimacionDeEspera = $("<div>", { class: "fvaLoader" }).append($("<div>"), $("<div>"), $("<div>"));
    var elCampoParaAccesibilidad = $("<div>", { class: "fvaElementoOculto" });
    var elCampoParaCopiar = $("<input/>", { class: "fvaElementoOculto" });
    var elMensajeDeCopiado = $("<div>", { class: "fvaMensajeDeCopiado" }).css({ display: "none" });
    var elTextoDeCopieElCodigo = "Para confirmar la transacci&oacute;n, seleccione el siguiente c&oacute;digo de verificaci&oacute;n en GAUDI";
    var elTextoDeAyudaQueEsFirmadorBccr = "&iquest;Qu&eacute; es GAUDI?";
    var laDescripcionDelFormato = '<div class="fvaDescripcionDelFormato"><span class="fvaCodLetra">Letra</span><span class="fvaDescripcionDelFormatoSeparador"> | </span><span>N&uacute;mero</span></div>';
    var elTituloDelResumen = '<div class="fvaTituloDelResumen">Resumen de la transacci&oacute;n:</div>';
    var laAdvertenciaAlUsuario = '<div class="fvaAdvertencia">El c&oacute;digo de verificaci&oacute;n es para su uso exclusivo y personal. No lo facilite por tel&eacute;fono o correo electr&oacute;nico a ninguna persona.</div>';
    var elResumenDelDocumento = $("<div>", { class: "fvaResumen" });
    var elIconoDeAyuda = $("<img>", { src: laConfiguracion.Imagenes.Ayuda, alt: "Ayuda", height: "21", width: "21" });
    var elContenidoDeTextoCopieElCodigo = $("<div>", { class: "fvaContenidoDeTextoCopieElCodigo" });
    var laUrlParaConsultarLaSolicitud = laConfiguracion.UrlConsultaFirma;
    var elBotonDeCopiar = $("<input/>", { class: "fvaElBotonDeCopiar", value: "Copiar", type: "button" });
    ConfigureElSitioParaRealizarSolicitudes();

    function ConfigureElSitioParaRealizarSolicitudes() {
        elBotonDeAceptar.bind("click", InvoqueASolicitudNoRealizada);
        $("body").append(laVentanaModal);
        $("body").append(elFondoOscuro);
        $("body").append(elCampoParaAccesibilidad);
        $("body").append(elCampoParaCopiar);
        $("body").append(elMensajeDeCopiado);
        CreeLaVentanaModal();
        function CreeLaVentanaModal() {
            AgregueElEstilo();
            elContenidoDelCuerpo.append(elContenidoDeTexto, laAnimacionDeEspera, elBotonDeAceptar);
            laVentanaModal.append(elContenidoDelCuerpo);
            function AgregueElEstilo() {
                $("head").append('<link rel="stylesheet" href="' + laConfiguracion.UrlCSS+'" type="text/css" />');
            }
        }
        function InvoqueASolicitudNoRealizada() {
            OculteLaVentanaModal();
            laConfiguracion.SolicitudNoRealizada();
        }
    }

    function EnvieLaSolicitud() {
        RemuevaElBordeDeError();
        AsigneElTextoALaVentana(laConfiguracion.TextoSolicitando);
        OculteElBotonDeAceptar();
        MuestreLaAnimacionDeEspera();
        MuestreLaVentanaModal();
        RealiceLaSolicitud();

        function RealiceLaSolicitud() {
            var losDatosParaSolicitar = laConfiguracion.DatosParaSolicitar();
            $.ajax({
                url: laConfiguracion.UrlParaSolicitar,
                type: "POST",
                dataType: "text json",
                processData: false,
                data: losDatosParaSolicitar,
                contentType: false,
                cache: false,
                global: false,
                success: SolicitudCompletada,
                error: MuestreElMensajeDeErrorAlSolicitar
            });
        }

        function SolicitudCompletada(laRespuesta) {
            var fueExitosaLaSolicitud = laRespuesta.FueExitosaLaSolicitud;
            var elTiempoMaximoDeFirmaEnMiliSegundos = ObtengaElValorEnMiliSegundos(laRespuesta.TiempoMaximoDeFirmaEnSegundos);
            var elTiempoDeEsperaParaConsultarLaFirmaEnMiliSegundos = ObtengaElValorEnMiliSegundos(laRespuesta.TiempoDeEsperaParaConsultarLaFirmaEnSegundos);
            var elCodigoDeVerificacion = laRespuesta.CodigoDeVerificacion;
            var elIdDeLaSolicitud = laRespuesta.IdDeLaSolicitud;
            var elResumenDocumento = laRespuesta.ResumenDelDocumento;
            var seTerminoElTiempoDeFirma = false;
            if (fueExitosaLaSolicitud) {
                var elCodigoDeVerificacionFormateado = FormateeElCodigoDeVerificacion(elCodigoDeVerificacion);
                elCodigoConBotonCopiar.html("").append(elCodigoDeVerificacionFormateado, elBotonDeCopiar);
                if (elResumenDocumento === undefined || elResumenDocumento === null) {
                    elResumenDelDocumento.html("");
                    elTituloDelResumen = "";
                } else {
                    elResumenDelDocumento.html(elResumenDocumento);
                }
                NotifiqueCuandoSeTermineElTiempoMaximoDeFirma();
                var elContenido = ObtengaElContenidoConCodigoDeVerificacion();
                AsigneElTextoALaVentana(elContenido);
                ConsulteLaSolicitudConEspera();
            } else {
                MuestreElMensajeDeErrorDeLaRespuesta(laRespuesta);
            }
            function ObtengaElContenidoConCodigoDeVerificacion() {
                elContenidoDeTextoCopieElCodigo.html(elTextoDeCopieElCodigo);
                elAcordeon.append(elIconoDeAyuda, elToolTipText);
                elPanelAcordeon.append(laConfiguracion.ImagenDelFirmador);
                elContenidoDeCopieCodigo.append(elContenidoDeTextoCopieElCodigo, elAcordeon);
                elPanelAcordeon.css({ "max-height": "0px" });
                elAcordeon.removeClass("active");
                elToolTipText.html(elTextoDeAyudaQueEsFirmadorBccr);
                elAcordeon.click(function () {
                    this.classList.toggle("active");
                    if (elPanelAcordeon[0].style.maxHeight != "0px") {
                        elPanelAcordeon[0].style.maxHeight = "0px";
                        elToolTipText.html(elTextoDeAyudaQueEsFirmadorBccr);
                    } else {
                        elPanelAcordeon[0].style.maxHeight = elPanelAcordeon[0].scrollHeight + "px";
                        elToolTipText.html("Ocultar");
                    }
                });
                elBotonDeCopiar.click(CopieElCodigoDeVerificacionAlPortapapeles);
                var elContenido = $("<div>").append(elContenidoDeCopieCodigo, elCodigoConBotonCopiar, laDescripcionDelFormato, elTituloDelResumen, elResumenDelDocumento, laAdvertenciaAlUsuario, elPanelAcordeon);
                return elContenido;
            }
            function CopieElCodigoDeVerificacionAlPortapapeles() {
                elCampoParaCopiar.val(elCodigoDeVerificacion);
                elCampoParaCopiar.select();
                var elMensaje = "";
                try {
                    var siPudoCopiar = document.execCommand("copy");
                    if (siPudoCopiar) {
                        elMensaje = "C&oacute;digo de verificaci&oacute;n copiado";
                    } else {
                        elMensaje = "No se ha podido copiar el c&oacute;digo de verificaci&oacute;n";
                    }
                } catch (elError) {
                    elMensaje = "No se ha podido copiar el c&oacute;digo de verificaci&oacute;n";
                }
                elMensajeDeCopiado.html(elMensaje);
                if (elMensajeDeCopiado[0].style.display !== "block") {
                    elMensajeDeCopiado.fadeIn("slow", function () {
                        $(this).delay(1500).fadeOut("slow");
                    });
                }
            }

            function NotifiqueCuandoSeTermineElTiempoMaximoDeFirma() {
                setTimeout(GuardeCuandoSeTermineElTiempoMaximoDeFirma, elTiempoMaximoDeFirmaEnMiliSegundos);
            }

            function GuardeCuandoSeTermineElTiempoMaximoDeFirma() {
                seTerminoElTiempoDeFirma = true;
            }

            function ObtengaElValorEnMiliSegundos(elValor) {
                return 1000 * parseInt(elValor);
            }
            
            function FormateeElCodigoDeVerificacion(elCodigoDeVerificacion) {
                var elCodigoFormateado = "<div>";
                var elCaracterFormateado;
                var elCaracter;
                var laCantidadDeCaracteres = elCodigoDeVerificacion.length;
                for (var elIndiceActual = 0; elIndiceActual < laCantidadDeCaracteres; elIndiceActual++) {
                    elCaracter = elCodigoDeVerificacion[elIndiceActual];
                    if (EsUnNumero(elCaracter)) {
                        elCaracterFormateado = "<span>" + elCaracter + "</span>";
                    } else {
                        elCaracterFormateado = '<span class="fvaCodLetra">' + elCaracter + "</span>";
                    }
                    elCodigoFormateado = elCodigoFormateado + elCaracterFormateado;
                }
                return elCodigoFormateado + "</div>";
            }

            function EsUnNumero(elCaracter) {
                return !isNaN(elCaracter);
            }

            function ConsulteLaSolicitud() {
                var losDatosParaConsultar = { IdDeLaSolicitud: elIdDeLaSolicitud };
                $.ajax({
                    url: laUrlParaConsultarLaSolicitud,
                    jsonp: "callback",
                    dataType: "jsonp",
                    data: losDatosParaConsultar,
                    global: false,
                    success: VerifiqueQueSeCompletoLaSolicitud,
                    error: MuestreElMensajeDeErrorAlSolicitar
                });
            }

            function ConsulteLaSolicitudConEspera() {
                setTimeout(ConsulteLaSolicitud, elTiempoDeEsperaParaConsultarLaFirmaEnMiliSegundos);
            }

            function VerifiqueQueSeCompletoLaSolicitud(laRespuesta) {
                if (laRespuesta.SeRealizo == true) {
                    NotifiqueQueSeCompletoLaSolicitud(laRespuesta);
                } else {
                    if (seTerminoElTiempoDeFirma == true) {
                        MuestreElMensajeDeErrorAlSolicitar();
                    } else {
                        ConsulteLaSolicitudConEspera();
                    }
                }
            }
        }

        function NotifiqueQueSeCompletoLaSolicitud(laRespuesta) {
            if (laRespuesta.FueExitosa == true) {
                NotifiqueQueSeCompletoLaSolicitudConExito();
            } else {
                MuestreElMensajeDeErrorDeLaRespuesta(laRespuesta);
            }
        }

        function MuestreElMensajeDeErrorDeLaRespuesta(laRespuesta) {
            if (laRespuesta.DebeMostrarElError == true) {
                NotifiqueQueSeCompletoLaSolicitudConError(laRespuesta.DescripcionDelError);
            } else {
                NotifiqueQueSeCompletoLaSolicitudConErrorInesperado();
            }
        }

        function NotifiqueQueSeCompletoLaSolicitudConExito() {
            OculteLaVentanaModal();
            laConfiguracion.SolicitudRealizada();
        }

        function MuestreElMensajeDeErrorAlSolicitar() {
            NotifiqueQueSeCompletoLaSolicitudConErrorInesperado();
        }

        function NotifiqueQueSeCompletoLaSolicitudConError(elTextoAMostrar) {
            var elTextoAMostrar = laConfiguracion.TituloMensaje + '<div class="fvaMargenDeContenido fvaColorMensajeSecundario">' + elTextoAMostrar + "</div>";
            MuestreElBordeDeError();
            AsigneElTextoALaVentana(elTextoAMostrar);
            OculteLaAnimacionDeEspera();
            MuestreElBotonDeAceptar();
        }

        function NotifiqueQueSeCompletoLaSolicitudConErrorInesperado() {
            var T = "<p>Estimado suscriptor, se presentó un problema a la hora de realizar este proceso.</p>";
            var V = '<p class="fvaColorMensajeSecundario">Pasos a seguir:</p><ol><li>Verificar si el Agente GAUDI se encuentra en estado conectado.<div class="fvaIconoFirmadorConectado"></div></li><li>Intentar nuevamente.</li>';
            var S = '<p class="fvaContenidoParaErrorGeneralMensajeFinal">En caso de no corregirse, favor contactar al centro de soporte.</p>';
            var U = T + '<div class="fvaMargenDeContenido fvaColorMensajeSecundario fvaContenidoParaErrorGeneral">' + V + "</div>" + S;
            MuestreElBordeDeError();
            AsigneElTextoALaVentana(U);
            OculteLaAnimacionDeEspera();
            MuestreElBotonDeAceptar();
        }
    }

    function AsigneElTextoALaVentana(elTexto) {
        elContenidoDeTexto.html(elTexto);
        EjecuteLaAccesibilidad(elTexto);

        function EjecuteLaAccesibilidad(elTexto) {
            var elInputParaAccesibilidad = $("<input/>", { type: "text" });
            elInputParaAccesibilidad.val(elTexto);
            elCampoParaAccesibilidad.empty();
            elCampoParaAccesibilidad.append(elInputParaAccesibilidad);
            elInputParaAccesibilidad.focus();
        }
    }

    function MuestreLaVentanaModal() {
        elFondoOscuro.css({ display: "block" });
        laVentanaModal.css({ display: "block" });
    }

    function OculteElBotonDeAceptar(){
        elBotonDeAceptar.css({ display: "none" });
    }

    function MuestreLaAnimacionDeEspera() {
        laAnimacionDeEspera.css({ display: "block" });
    }

    function OculteLaVentanaModal() {
        elFondoOscuro.css({ display: "none" });
        laVentanaModal.css({ display: "none" });
    }

    function OculteLaAnimacionDeEspera() {
        laAnimacionDeEspera.css({ display: "none" });
    }

    function MuestreElBotonDeAceptar() {
        elBotonDeAceptar.css({ display: "inline-block" });
    }

    function RemuevaElBordeDeError() {
        elContenidoDelCuerpo.removeClass("fvaBordeDeError");
    }

    function MuestreElBordeDeError() {
        elContenidoDelCuerpo.addClass("fvaBordeDeError");
    }
};

var FvaAutenticador = function (laConfiguracion) {
    laConfiguracion = $.extend({
        ParaAutenticarse: "",
        IdDelBotonDeAutenticar: "BotonDeAutenticar",
        UrlParaSolicitarLaAutenticacion: "",
        DominioDelSitio: "" }, laConfiguracion);

    var elBotonDeAutenticar = $("#" + laConfiguracion.IdDelBotonDeAutenticar);
    var laImagenDelFirmador = $("<img>", { src: laConfiguracion.Imagenes.Autenticador, alt: "Imagen de ayuda del Autenticador" });

    var laConfiguracionParaElClienteInterno = {
        TextoSolicitando: "Procesando su solicitud de autenticaci&oacute;n...",
        DominioDelSitio: laConfiguracion.DominioDelSitio,
        MensajeDeError: laConfiguracion.MensajeDeError,
        ImagenDelFirmador: laImagenDelFirmador,
        DatosParaSolicitar: ObtengaLosDatosParaSolicitar,
        SolicitudRealizada: laConfiguracion.AutenticacionRealizada,
        SolicitudNoRealizada: laConfiguracion.AutenticacionNoRealizada,
        UrlParaSolicitar: laConfiguracion.UrlParaSolicitarLaAutenticacion,
        TituloMensaje: "No se logró realizar la autenticación por el siguiente motivo.",
        Imagenes: laConfiguracion.Imagenes,
        UrlConsultaFirma: laConfiguracion.UrlConsultaFirma,
        UrlCSS: laConfiguracion.UrlCSS,
        UsoAutenticacion: true
    };

    var elTextoTooltipParaIdentificacion = "<div class='fvaToolTipIdentificacionTitulo'>Formato de la identificaci&oacute;n</div><ul><li><span>Nacional:</span><span>00-0000-0000</span></li><li><span>DIDI:</span><span>500000000000</span></li><li><span>DIMEX:</span><span>100000000000</span></li></li>";
    var elTextoInformativo = "Para autenticarse " + laConfiguracion.ParaAutenticarse + ", primero debe ingresar su n&uacute;mero de identificaci&oacute;n:";
    var laEntradaDeLaIdentificacion = $("<input>", { type: "text" });
    var elContenidoParaMensajesDeError = $("<div>", { class: "fvaMensajeErrorIdentificacion fvaMargenDeContenido" });
    var elBotonParaSolicitarLaAutenticacion = $("<div>", { class: "fvaBoton" });
    var elBotonCancelar = $("<div>", { class: "fvaBoton" });
    var elContenidoParaLosBotones = $("<div>", { class: "fvaMargenDeContenido" });
    var elContenidoParaIdentificacion = $("<div>", { class: "fvaContenidoParaIdentificacion" });
    var laPosicionDelToolTipIdentificacion = $("<div>", { class: "fvaPosicionDelToolTipIdentificacion" });
    var elToolTipIdentificacion = $("<div>", { class: "fvaToolTipIdentificacion" });
    var elContenidoParaElMensaje = $("<div>", { class: "fvaMargenDeContenido" });
    var i = "https://ayudaenlinea.bccr.fi.cr/ucontent/6294cf05198d40b6aaaddca4447b4016_es-ES/sim/html/sim_auto_playback.htm";
    var elContenidoParaDelTipoDeIdentificacion = $("<div>", { class: "fvaContenidoParaTipoIdentificacion" });
    var m = '<div class="fvaContenidoParaInformacionDeConectado"><div>Recuerde que para poder realizarla deber&aacute;:</div><ul><li>Insertar la tarjeta de firma digital en el lector o computadora.</li><li>El Agente GAUDI debe estar instalado y en estado conectado. <div class="fvaIconoFirmadorConectado"></div></li></ul><div>Cualquier consulta sobre el uso de GAUDI, puede utilizar la gu&iacute;a <a href="' +
        i +
        '" target="_blank">Uso de GAUDI</a>.</div></div>';
    var elRadioBotonNacional = $("<div>", { class: "fvaRadioBoton" });
    var elRadioBotonExtranjero = $("<div>", { class: "fvaRadioBoton" });
    var elClienteInterno = new FvaClienteInterno(laConfiguracionParaElClienteInterno);

    elBotonDeAutenticar.click(function () {
        var elContenido = ObtengaLaVistaDeSolicitudDeIdentificacion();
        elClienteInterno.RemuevaElBordeDeError();
        elClienteInterno.AsigneElTextoALaVentana(elContenido);
        elClienteInterno.OculteElBotonDeAceptar();
        elClienteInterno.OculteLaAnimacionDeEspera();
        elClienteInterno.MuestreLaVentanaModal();
        laEntradaDeLaIdentificacion.focus();
    });

    function ObtengaLaVistaDeSolicitudDeIdentificacion() {
        $(elBotonParaSolicitarLaAutenticacion).unbind();
        $(laEntradaDeLaIdentificacion).unbind("keyup");
        $(elBotonCancelar).unbind();
        $(elRadioBotonNacional).unbind();
        $(elRadioBotonExtranjero).unbind();

        var elContenido = $("<div>");
        elBotonParaSolicitarLaAutenticacion.html("Autenticar");
        elBotonCancelar.html("Cancelar");
        elRadioBotonNacional.html("<input type='radio' name='laOpcionNacional' id ='laOpcionNacional' value='laOpcionNacional' checked>Nacional ");
        elRadioBotonExtranjero.html("<input type='radio' name='laOpcionExtranjero' id ='laOpcionExtranjero' value='laOpcionExtranjero'>Extranjero");
        elContenidoParaElMensaje.html(elTextoInformativo);
        elToolTipIdentificacion.html(elTextoTooltipParaIdentificacion);
        laPosicionDelToolTipIdentificacion.append(elToolTipIdentificacion);
        elContenidoParaIdentificacion.append(laEntradaDeLaIdentificacion, laPosicionDelToolTipIdentificacion);
        elContenidoParaDelTipoDeIdentificacion.append(elRadioBotonNacional, elRadioBotonExtranjero);
        elContenidoParaLosBotones.append(elBotonParaSolicitarLaAutenticacion, elBotonCancelar);
        laEntradaDeLaIdentificacion.val("");
        elContenidoParaMensajesDeError.html("");

        elBotonParaSolicitarLaAutenticacion.click(function () {
            ProceseLaAutenticacion();
        });

        laEntradaDeLaIdentificacion.keyup(function (event) {
            if (event.keyCode === 13) {
                ProceseLaAutenticacion();
            }
            if (laEntradaDeLaIdentificacion.val().length > 1 && laEntradaDeLaIdentificacion.val().startsWith("0") == false && $("#laOpcionNacional").is(":checked")) {
                laEntradaDeLaIdentificacion.val("");
            }
            if (laEntradaDeLaIdentificacion.val().length > 1 && laEntradaDeLaIdentificacion.val().startsWith("5") == false && laEntradaDeLaIdentificacion.val().startsWith("1") == false && $("#laOpcionExtranjero").is(":checked")) {
                laEntradaDeLaIdentificacion.val("");
            }
            if (laEntradaDeLaIdentificacion.val().length == 1 && laEntradaDeLaIdentificacion.val() != "0" && $("#laOpcionNacional").is(":checked")) {
                laEntradaDeLaIdentificacion.val("0" + laEntradaDeLaIdentificacion.val());
            }
            if (laEntradaDeLaIdentificacion.val().length == 1 && laEntradaDeLaIdentificacion.val() != "5" && laEntradaDeLaIdentificacion.val() != "1" && $("#laOpcionExtranjero").is(":checked")) {
                laEntradaDeLaIdentificacion.val("");
            }
        });

        elBotonCancelar.click(function () {
            elClienteInterno.OculteLaVentanaModal();
        });

        elRadioBotonNacional.click(function () {
            $("#laOpcionNacional").prop("checked", true);
            laEntradaDeLaIdentificacion.maskCI("00-0000-0000", { reverse: true, placeholder: "00-0000-0000" });
            laEntradaDeLaIdentificacion.val("");
            $("#laOpcionExtranjero").prop("checked", false);
        });

        elRadioBotonExtranjero.click(function () {
            $("#laOpcionExtranjero").prop("checked", true);
            laEntradaDeLaIdentificacion.maskCI("000000000000", { reverse: true, placeholder: "000000000000" });
            laEntradaDeLaIdentificacion.val("");
            $("#laOpcionNacional").prop("checked", false);
        });
        elContenido.append(elContenidoParaElMensaje, elContenidoParaIdentificacion, elContenidoParaDelTipoDeIdentificacion, m, elContenidoParaMensajesDeError, elContenidoParaLosBotones);
        laEntradaDeLaIdentificacion.maskCI("00-0000-0000", { reverse: true, placeholder: "00-0000-0000" });
        return elContenido;
    }

    function ProceseLaAutenticacion() {
        var esValido = ValideElFormatoDeLaIdentificacion();
        if (esValido) {
            elClienteInterno.EnvieLaSolicitud();
        } else {
            elClienteInterno.MuestreElBordeDeError();
            elContenidoParaMensajesDeError.html("El formato de la identificaci&oacute;n es incorrecto.");
        }

        function ValideElFormatoDeLaIdentificacion() {
            var laIdentificacion = laEntradaDeLaIdentificacion.val();
            return FvaValidador.ValideLaIdentificacion(laIdentificacion);
        }
    }

    function ObtengaLosDatosParaSolicitar() {
        var losDatos = laConfiguracion.ObtengaLosDatosParaSolicitarLaAutenticacion();
        var laIdentificacion = laEntradaDeLaIdentificacion.val();
        if (losDatos === undefined) {
            losDatos = new FormData();
        }
        losDatos.append("Identificacion", laIdentificacion);
        return losDatos;
    }
};

var FvaFirmador = function (laConfiguracion) {
    laConfiguracion = $.extend({
        IdDelBotonDeFirmar: "BotonDeFirmar",
      //  UrlParaSolicitarLaFirma: "",
        DominioDelSitio: "" }, laConfiguracion);
    var elBotonDeFirmar = $("#" + laConfiguracion.IdDelBotonDeFirmar);
    var laImagenDelFirmador = $("<img>", { src: laConfiguracion.Imagenes.Firma, alt: "Imagen de ayuda del Firmador" });
    var laConfiguracionParaElClienteInterno = {
        TextoSolicitando: "Procesando su solicitud de firma...",
        DominioDelSitio: laConfiguracion.DominioDelSitio,
        MensajeDeError: laConfiguracion.MensajeDeError,
        ImagenDelFirmador: laImagenDelFirmador,
        DatosParaSolicitar: ObtengaLosDatosParaSolicitar,
        SolicitudRealizada: laConfiguracion.FirmaRealizada,
        SolicitudNoRealizada: laConfiguracion.FirmaNoRealizada,
        UrlParaSolicitar: laConfiguracion.UrlParaSolicitarLaFirma,
        TituloMensaje: "No se logró realizar la firma por el siguiente motivo.",
        Imagenes: laConfiguracion.Imagenes,
        UrlConsultaFirma: laConfiguracion.UrlConsultaFirma,
        UrlCSS: laConfiguracion.UrlCSS,
        UsoAutenticacion: false
    };

    var elClienteInterno = new FvaClienteInterno(laConfiguracionParaElClienteInterno);

    elBotonDeFirmar.click(function () {
        elClienteInterno.EnvieLaSolicitud();
    });

    function ObtengaLosDatosParaSolicitar() {
        return laConfiguracion.ObtengaLosDatosParaSolicitarLaFirma();
    }
};

var FvaValidador = {
    ValideLaIdentificacion: function (laIdentificacion) {
        var laExpresionRegularNacional = /^0[1-9]{1}-\d{4}-\d{4}$/;
        var laExpresionRegularDIDI = /^5[0-9]{11}$/;
        var laExpresionRegularDIMEX = /^1[0-9]{11}$/;
        var esValido;

        if (laExpresionRegularNacional.test(laIdentificacion) ||
         laExpresionRegularDIDI.test(laIdentificacion) ||
         laExpresionRegularDIMEX.test(laIdentificacion)) {
            esValido = true;
        } else {
            esValido = false;
        }
        return esValido;
    }
};

/*-------------  Metodos Mask ---------------*/
(function (factory, jQuery, Zepto) {

    if (typeof define === "function" && define.amd) {
        define(["jquery"], factory);
    } else {
        if (typeof exports === "object") {
            module.exports = factory(require("jquery"));
        } else {
            factory(jQuery || Zepto);
        }
    }
})
(function ($) {
    var Mask = function (el, maskCI, options) {
        var p = {
            invalid: [],
            getCaret: function () {
                try {
                    var sel,
                        pos = 0,
                        ctrl = el.get(0),
                        dSel = document.selection,
                        cSelStart = ctrl.selectionStart;

                    // IE Support
                    if (dSel && navigator.appVersion.indexOf("MSIE 10") === -1) {
                        sel = dSel.createRange();
                        sel.moveStart("character", -k.val().length);
                        pos = sel.text.length;
                    }
                        // Firefox support
                    else {
                        if (cSelStart || cSelStart === "0") {
                           pos = cSelStart;
                        }
                   }
                    return pos;
                } catch (e) { }
            },
            setCaret: function (pos) {
                try {
                    if (el.is(":focus")) {
                        var range, ctrl = el.get(0);

                        // Firefox, WebKit, etc..
                        if (ctrl.setSelectionRange) {
                            ctrl.setSelectionRange(pos, pos);
                        } else { // IE
                            range = ctrl.createTextRange();
                            range.collapse(true);
                            range.moveEnd("character", pos);
                            range.moveStart("character", pos);
                            range.select();
                            }
                        }
                    } catch (e) {}
            },
            events: function () {
                el.on("keydown.maskCI", function (e) {
                    el.data("maskCI-keycode", e.keyCode || e.which);
                    el.data("maskCI-previus-value", el.val());
                    el.data("maskCI-previus-caret-pos", p.getCaret());
                    p.maskDigitPosMapOld = p.maskCIDigitPosMap;
                })
                .on($.jMaskGlobals.useInput ? "input.maskCI" : "keyup.maskCI", p.behaviour)
                .on("paste.maskCI drop.maskCI", function () {
                    setTimeout(function () {
                        el.keydown().keyup();
                    }, 100);
                })
                .on("change.maskCI", function () {
                    el.data("changed", true);
                })
                .on("blur.maskCI", function () {
                    if (oldValue !== p.val() && !el.data("changed")) {
                        el.trigger("change");
                    }
                    el.data("changed", false);
                })
                // it's very important that this callback remains in this position
                // otherwhise oldValue it's going to work buggy
                .on("blur.maskCI", function () {
                    oldValue = p.val();
                })
                // select all text on focus
                .on("focus.maskCI", function (e) {
                    if (options.selectOnFocus === true) {
                        $(e.target).select();
                    }
                })
                // clear the value if it not complete the mask
               .on("focusout.maskCI", function () {
                    if (options.clearIfNotMatch && !regexMask.test(p.val())) {
                        p.val("");
                    }
                });
            },
            getRegexMask: function () {
                var maskCIChunks = [], translation, pattern, optional, recursive, oRecursive, r;
                for (var i = 0; i < maskCI.length; i++) {
                    translation = jMask.translation[maskCI.charAt(i)];
                    if (translation) {
                        pattern = translation.pattern.toString().replace(/.{1}$|^.{1}/g, "");
                        optional = translation.optional;
                        recursive = translation.recursive;
                        if (recursive) {
                            maskCIChunks.push(maskCI.charAt(i));
                            oRecursive = { digit: maskCI.charAt(i), pattern: pattern };
                        } else {
                            maskCIChunks.push(!optional && !recursive ? pattern : pattern + "?");
                        }
                   } else {
                        maskCIChunks.push(maskCI.charAt(i).replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&"));
                    }
                }

                r = maskCIChunks.join("");

                if (oRecursive) {
                    r = r.replace(new RegExp("(" + oRecursive.digit + "(.*" + oRecursive.digit + ")?)"), "($1)?")
                         .replace(new RegExp(oRecursive.digit, "g"), oRecursive.pattern);
                }

                return new RegExp(r);
            },
            destroyEvents: function () {
                el.off(["input", "keydown", "keyup", "paste", "drop", "blur", "focusout", ""].join(".maskCI "));
            },
            val: function (v) {
                var isInput = el.is("input"),
                    method = isInput ? "val" : "text",
                    r;

                if (arguments.length > 0) {
                    if (el[method]() !== v) {
                        el[method](v);
                    }
                    r = el;
                } else {
                    r = el[method]();
                }

                return r;
            },
            calculateCaretPosition: function () {
                var oldVal = el.data("maskCI-previus-value") || "",
                    newVal = p.getMasked(),
                    caretPosNew = p.getCaret();
                if (oldVal !== newVal) {
                    var caretPosOld = el.data("maskCI-previus-caret-pos") || 0,
                        newValL = newVal.length,
                        oldValL = oldVal.length,
                        maskCIDigitsBeforeCaret = 0,
                        maskCIDigitsAfterCaret = 0,
                        maskCIDigitsBeforeCaretAll = 0,
                        maskCIDigitsBeforeCaretAllOld = 0,
                        i = 0;
                    for (i = caretPosNew; i < newValL; i++) {
                        if (!p.maskCIDigitPosMap[i]) {
                            break;
                        }
                        maskCIDigitsAfterCaret++;
                    }
                    for (i = caretPosNew - 1; i >= 0; i--) {
                        if (!p.maskCIDigitPosMap[i]) {
                            break;
                        }
                        maskCIDigitsBeforeCaret++;
                    }
                    for (i = caretPosNew - 1; i >= 0; i--) {
                        if (p.maskCIDigitPosMap[i]) {
                            maskCIDigitsBeforeCaretAll++;
                        }
                    }

                    for (i = caretPosOld - 1; i >= 0; i--) {
                        if (p.maskDigitPosMapOld[i]) {
                            maskCIDigitsBeforeCaretAllOld++;
                        }
                    }
                    if (caretPosNew > oldValL) {
                        // if the cursor is at the end keep it there
                        caretPosNew = newValL;
                    } else {
                     if (caretPosOld >= caretPosNew && caretPosOld !== oldValL) {
                        if (!p.maskDigitPosMapOld[caretPosNew]) {
                            var caretPos = caretPosNew;
                            caretPosNew -= maskCIDigitsBeforeCaretAllOld - maskCIDigitsBeforeCaretAll;
                            caretPosNew -= maskCIDigitsBeforeCaret;
                            if (p.maskCIDigitPosMap[caretPosNew]) {
                                caretPosNew = caretPos;
                        }
                       }
                            } else {
                                if (caretPosNew > caretPosOld) {
                                    caretPosNew += maskCIDigitsBeforeCaretAll - maskCIDigitsBeforeCaretAllOld;
                                    caretPosNew += maskCIDigitsAfterCaret;
                                }
                            }
                        }
                    }
                   return caretPosNew;
            },
            behaviour: function (e) {
                e = e || window.event;
                p.invalid = [];
                var keyCode = el.data("maskCI-keycode");
                if ($.inArray(keyCode, jMask.byPassKeys) === -1) {
                    var newVal = p.getMasked(),
                        caretPos = p.getCaret();
                    setTimeout(function () {
                        p.setCaret(p.calculateCaretPosition());
                    }, 10);
                    p.val(newVal);
                    p.setCaret(caretPos);
                    return p.callbacks(e);
                }
            },
            getMasked: function (skipMaskChars, val) {
                var buf = [],
                    value = val === undefined ? p.val() : val + "",
                    m = 0, maskLen = maskCI.length,
                    v = 0, valLen = value.length,
                    offset = 1, addMethod = 'push',
                    resetPos = -1,
                    maskDigitCount = 0,
                    maskDigitPosArr = [],
                    lastMaskChar,
                    check;
                if (options.reverse) {
                    addMethod = "unshift";
                    offset = -1;
                    lastMaskChar = 0;
                    m = maskLen - 1;
                    v = valLen - 1;
                    check = function () {
                        return m > -1 && v > -1;
                    };
                } else {
                    lastMaskChar = maskLen - 1;
                    check = function () {
                        return m < maskLen && v < valLen;
                    };
                }

                var lastUntranslatedMaskChar;
                while (check()) {
                    var maskDigit = maskCI.charAt(m),
                        valDigit = value.charAt(v),
                        translation = jMask.translation[maskDigit];
                    if (translation) {
                        if (valDigit.match(translation.pattern)) {
                            buf[addMethod](valDigit);
                            if (translation.recursive) {
                                if (resetPos === -1) {
                                    resetPos = m;
                                } else if (m === lastMaskChar) {
                                    m = resetPos - offset;
                                }

                                if (lastMaskChar === resetPos) {
                                    m -= offset;
                                }
                            }

                            m += offset;
                        } else if (valDigit === lastUntranslatedMaskChar) {
                            // matched the last untranslated (raw) mask character that we encountered
                            // likely an insert offset the mask character from the last entry; fall
                            // through and only increment v
                            maskDigitCount--;
                            lastUntranslatedMaskChar = undefined;
                        } else if (translation.optional) {
                            m += offset;
                            v -= offset;
                        } else if (translation.fallback) {
                            buf[addMethod](translation.fallback);
                            m += offset;
                            v -= offset;
                        } else {
                            p.invalid.push({ p: v, v: valDigit, e: translation.pattern });
                        }

                        v += offset;
                    } else {
                        if (!skipMaskChars) {
                            buf[addMethod](maskDigit);
                        }

                        if (valDigit === maskDigit) {
                            maskDigitPosArr.push(v);
                            v += offset;
                        } else {
                            lastUntranslatedMaskChar = maskDigit;
                            maskDigitPosArr.push(v + maskDigitCount);
                            maskDigitCount++;
                        }
                        m += offset;
                    } 
                }
                var lastMaskCharDigit = maskCI.charAt(lastMaskChar);
                if (maskLen === valLen + 1 && !jMask.translation[lastMaskCharDigit]) {
                    buf.push(lastMaskCharDigit);
                }

                var newVal = buf.join("");
                p.mapMaskdigitPositions(newVal, maskDigitPosArr, valLen);
                return newVal;
            },
            mapMaskdigitPositions: function (newVal, maskDigitPosArr, valLen) {
                var maskDiff = options.reverse ? newVal.length - valLen : 0;
                p.maskCIDigitPosMap = {};
                for (var i = 0; i < maskDigitPosArr.length; i++) {
                    p.maskCIDigitPosMap[maskDigitPosArr[i] + maskDiff] = 1;
                }
            },
            callbacks: function (e) {
                var val = p.val(),
                    changed = val !== oldValue,
                    defaultArgs = [val, e, el, options],
                    callback = function (name, criteria, args) {
                        if (typeof options[name] === 'function' && criteria) {
                            options[name].apply(this, args);
                        }
                    };
                callback("onChange", changed === true, defaultArgs);
                callback("onKeyPress", changed === true, defaultArgs);
                callback("onComplete", val.length === maskCI.length, defaultArgs);
                callback("onInvalid", p.invalid.length > 0, [val, e, el, p.invalid, options]);
            },
        };

        el = $(el);
        var jMask = this, oldValue = p.val(), regexMask;

        maskCI = typeof maskCI === "function" ? maskCI(p.val(), undefined, el, options) : maskCI;

        // public methods
        jMask.maskCI = maskCI;
        jMask.options = options;
        jMask.remove = function () {
            var caret = p.getCaret();
            p.destroyEvents();
            p.val(jMask.getCleanVal());
            p.setCaret(caret);
            return el;
        };

        // get value without mask
        jMask.getCleanVal = function () {
            return p.getMasked(true);
        };
        // get masked value without the value being in the input or element
        jMask.getMaskedVal = function (val) {
            return p.getMasked(false, val);
        };

        jMask.init = function (onlyMask) {
            onlyMask = onlyMask || false;
            options = options || {};

            jMask.clearIfNotMatch = $.jMaskGlobals.clearIfNotMatch;
            jMask.byPassKeys = $.jMaskGlobals.byPassKeys;
            jMask.translation = $.extend({}, $.jMaskGlobals.translation, options.translation);
            jMask = $.extend(true, {}, jMask, options);
            regexMask = p.getRegexMask();
            if (onlyMask) {
                p.events();
                p.val(p.getMasked());
            } else {
                if (options.placeholder) {
                    el.attr("placeholder", options.placeholder);
                }
                // this is necessary, otherwise if the user submit the form
                // and then press the "back" button, the autocomplete will erase
                // the data. Works fine on IE9+, FF, Opera, Safari.
                if (el.data("maskCI")) {
                    el.attr("autocomplete", "off");
                }

                // detect if is necessary let the user type freely.
                // for is a lot faster than forEach.
                for (var i = 0, maxlength = true; i < maskCI.length; i++) {
                    var translation = jMask.translation[maskCI.charAt(i)];
                    if (translation && translation.recursive) {
                        maxlength = false;
                        break;
                    }
                }

                if (maxlength) {
                    el.attr("maxlength", maskCI.length);
                }

                p.destroyEvents();
                p.events();

                var caret = p.getCaret();
                p.val(p.getMasked());
                p.setCaret(caret);
            }
        };

        jMask.init(!el.is("input"));
    };

    $.maskWatchers = {};
    var HTMLAttributes = function () {
        var input = $(this),
            options = {},
            prefix = "data-maskCI-",
            maskCI = input.attr("data-maskCI");
        if (input.attr(prefix + "reverse")) {
            options.reverse = true;
        }
        if (input.attr(prefix + "clearifnotmatch")) {
            options.clearIfNotMatch = true;
        }

        if (input.attr(prefix + "selectonfocus") === "true") {
            options.selectOnFocus = true;
        }
        if (notSameMaskObject(input, maskCI, options)) {
            return input.data("maskCI", new Mask(this, maskCI, options));
        }
    },
    notSameMaskObject = function (field, maskCI, options) {
        options = options || {};
        var maskObject = $(field).data("maskCI"),
            stringify = JSON.stringify,
            value = $(field).val() || $(field).text();
        try {
            if (typeof maskCI === "function") {
                maskCI = maskCI(value);
            }
            return typeof maskObject !== "object" || stringify(maskObject.options) !== stringify(options) || maskObject.maskCI !== maskCI;
        } catch (e) { }
    },

    eventSupported = function (eventName) {
        var el = document.createElement('div'), isSupported;
        eventName = "on" + eventName;
        isSupported = eventName in el;
        if (!isSupported) {
            el.setAttribute(eventName, "return;");
            isSupported = typeof el[eventName] === "function";
        }
        el = null;

        return isSupported;
    };
    $.fn.maskCI = function (maskCI, options) {
        options = options || {};
        var selector = this.selector,
            globals = $.jMaskGlobals,
            interval = globals.watchInterval,
            watchInputs = options.watchInputs || globals.watchInputs,
            maskFunction = function () {
                if (notSameMaskObject(this, maskCI, options)) {
                    return $(this).data("maskCI", new Mask(this, maskCI, options));
                }
            };

        $(this).each(maskFunction);
        if (selector && selector !== "" && watchInputs) {
            clearInterval($.maskWatchers[selector]);
            $.maskWatchers[selector] = setInterval(function () {
                $(document).find(selector).each(maskFunction);
            }, interval);
        }
        return this;
    };

    $.fn.masked = function (val) {
        return this.data("maskCI").getMaskedVal(val);
    };

    $.fn.unmask = function () {
        clearInterval($.maskWatchers[this.selector]);
        delete $.maskWatchers[this.selector];
        return this.each(function () {
            var dataMask = $(this).data("maskCI");
            if (dataMask) {
                dataMask.remove().removeData("maskCI");
            }
        });
    };
    $.fn.cleanVal = function () {
        return this.data("maskCI").getCleanVal();
    };
    $.applyDataMask = function (selector) {
        selector = selector || $.jMaskGlobals.maskElements;
        var $selector = selector instanceof $ ? selector : $(selector);
        $selector.filter($.jMaskGlobals.dataMaskAttr).each(HTMLAttributes);
    };
    var globals = {
        maskElements: "input,td,span,div",
        dataMaskAttr: "*[data-maskCI]",
        dataMask: true,
        watchInterval: 300,
        watchInputs: true,
        // old versions of chrome dont work great with input event
        useInput: !/Chrome\/[2-4][0-9]|SamsungBrowser/.test(window.navigator.userAgent) && eventSupported("input"),
        watchDataMask: false,
        byPassKeys: [9, 16, 17, 18, 36, 37, 38, 39, 40, 91],
        translation: {
            "0": { pattern: /\d/ },
            "9": { pattern: /\d/, optional: true },
            "#": { pattern: /\d/, recursive: true },
            A: { pattern: /[a-zA-Z0-9]/ },
            S: { pattern: /[a-zA-Z]/ }
        }
    };

    $.jMaskGlobals = $.jMaskGlobals || {};
    globals = $.jMaskGlobals = $.extend(true, {}, globals, $.jMaskGlobals);

    // looking for inputs with data-mask attribute
    if (globals.dataMask) {
        $.applyDataMask();
    }
    setInterval(function () {
        if ($.jMaskGlobals.watchDataMask) {
            $.applyDataMask();
        }
    }, globals.watchInterval);
}, window.jQuery, window.Zepto);
