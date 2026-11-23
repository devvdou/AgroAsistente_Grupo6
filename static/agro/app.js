document.addEventListener("DOMContentLoaded",()=>{
  const contexto=document.querySelector(".context-panel");
  if(contexto&&window.matchMedia("(max-width: 760px)").matches)contexto.removeAttribute("open");
  const modo=document.querySelector("[name='modo']");
  const cultivo=document.querySelector("[data-field='cultivo']");
  const superficie=document.querySelector("[data-field='superficie_m2']");
  const alternar=()=>{if(!modo)return;const ganadera=modo.value==="Ganadera";[cultivo,superficie].forEach(x=>{if(x)x.hidden=ganadera;});};
  if(modo){modo.addEventListener("change",alternar);alternar();}
  const pregunta=document.querySelector("[name='pregunta']"),contador=document.querySelector("#contador");
  const contar=()=>{if(contador&&pregunta)contador.textContent=`${pregunta.value.length}/300`;};
  if(pregunta){pregunta.addEventListener("input",contar);contar();}
  document.querySelectorAll("[data-loading-form]").forEach(form=>form.addEventListener("submit",()=>{const b=form.querySelector("[data-submit]");if(b){b.disabled=true;b.textContent="Consultando…";}}));
});
