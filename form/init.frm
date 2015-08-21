Off stats;
Off finalstats;
#ifndef `PIPES_'
  #message "No pipes found"
  .end;
#endif
#if `PIPES_' <= 0
  #message "No pipes found"
  .end;
#endif
#setexternal `PIPE1_'
#toexternal "OK"
#do FORMLINKLOOPVAR=1,1
  #fromexternal
#enddo
.end
