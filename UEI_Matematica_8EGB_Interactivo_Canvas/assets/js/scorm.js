
window.UEI_SCORM = (() => {
  let api=null, initialized=false;
  function findAPI(win){ let tries=0; while(win && tries<10){ if(win.API) return win.API; if(win.parent===win) break; win=win.parent; tries++; } try{ if(window.opener) return findAPI(window.opener); }catch(e){} return null; }
  function init(){ api=findAPI(window); if(!api) return false; try{ initialized=api.LMSInitialize('')==='true'; if(initialized){ const status=api.LMSGetValue('cmi.core.lesson_status'); if(!status || status==='not attempted') api.LMSSetValue('cmi.core.lesson_status','incomplete'); api.LMSCommit(''); } }catch(e){ initialized=false; } return initialized; }
  function setScore(raw,completed){ if(!initialized && !init()) return; try{ api.LMSSetValue('cmi.core.score.min','0'); api.LMSSetValue('cmi.core.score.max','100'); api.LMSSetValue('cmi.core.score.raw',String(Math.round(raw))); api.LMSSetValue('cmi.core.lesson_status',completed?'completed':'incomplete'); api.LMSCommit(''); }catch(e){} }
  function finish(){ if(initialized){ try{api.LMSCommit('');api.LMSFinish('');}catch(e){} initialized=false; } }
  window.addEventListener('load',init); window.addEventListener('beforeunload',finish);
  return {init,setScore,finish};
})();
