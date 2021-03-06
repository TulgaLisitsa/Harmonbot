
; https://api.twitch.tv/kraken/streams/imagrill
; https://tmi.twitch.tv/group/user/imagrill/chatters

on *:text:!points*:#:{
  if ($nick isop # || $nick == harmon758) && ($2) {
    if ($2 == on) {
      set %points.status. $+ $chan on 
      if (!%points. [ $+ [ $chan ] $+ ] .lines) { set %points. $+ $chan $+ .lines 1 }
      msg # !points is on.
      .timerpoints [ $+ [ $chan ] ] 0 60 .points $chan
    }
    elseif ($2 == off) {
      set %points.status. $+ $chan off
      msg # !points is off.
      .timerpoints [ $+ [ $chan ] ] off
    }
    elseif ($2 == top) {
      if ($3 isnum && $3 <= 100) { var %top_number = $int($3) }
      else { var %top_number = 10 }
      var %top_list = Top: 
      var %counter = 1
      var %top_sorted_points
      $points.writefiles($chan)
      while (%counter <= %top_number) {
        var %top_sorted_points = %top_sorted_points $read( [ points. [ $+ [ $chan ] $+ ] .sorted.txt ] , nt, %counter)
        inc %counter
      }
      var %previous = -1
      var %same_count = 0
      while ($numtok(%top_sorted_points, 32) > 0) {
        var %number = $gettok(%top_sorted_points, 1, 32)
        if (%previous == %number) { inc %same_count }
        else { %same_count = 0 }
        noop $read( [ points. [ $+ [ $chan ] $+ ] .txt ] , nst, %number)
        var %name_number = $readn
        %counter = %same_count
        while (%counter) {
          noop $read( [ points. [ $+ [ $chan ] $+ ] .txt ] , nst, %number, $calc($readn + 1))
          %name_number = $readn
          dec %counter
        }
        %counter = 1
        while (%name_number > $numtok(%points. [ $+ [ $chan ] $+ ] .names [ $+ [ %counter ] ], 32)) {
          %name_number = %name_number - $numtok(%points. [ $+ [ $chan ] $+ ] .names [ $+ [ %counter ] ], 32)
          inc %counter
        }
        var %name = $gettok(%points. [ $+ [ $chan ] $+ ] .names [ $+ [ %counter ] ], %name_number, 32)
        var %top_list = %top_list $capital(%name) $+ : $gettok(%top_sorted_points, 1, 32) 
        %top_sorted_points = $deltok(%top_sorted_points, 1, 32)
        %previous = %number
      }
      msg # %top_list
    }
    elseif ($points.findname($chan, $2)) {
      var %line = $points.findname($chan, $2)
      var %name_number = $findtok( [ %points. [ $+ [ $chan ] $+ ] .names [ $+ [ %line ] ] ] , $2, 1, 32)
      var %points = $gettok( [ %points. [ $+ [ $chan ] $+ ] .points [ $+ [ %line ] ] ] , %name_number, 32)
      var %rank = $points.findrank($chan, %points)
      var %time = $points.minstotime($gettok( [ %points. [ $+ [ $chan ] $+ ] .minutes [ $+ [ %line ] ] ] , %name_number, 32))
      msg # $capital($2) is rank %rank with %points points ( $+ %time $+ ).
    }
    elseif ($nick == $mid($chan,2-) || $nick == harmon758) {
      if ($2 == add) {
        if ($points.findname($chan, $3)) {
          if ($4 isnum) {
            var %line = $points.findname($chan, $3)
            var %name_number = $findtok( [ %points. [ $+ [ $chan ] $+ ] .names [ $+ [ %line ] ] ] , $3, 1, 32)
            var %points = $gettok( [ %points. [ $+ [ $chan ] $+ ] .points [ $+ [ %line ] ] ] , %name_number, 32) + $4
            set %points. $+ $chan $+ .points $+ %line $puttok( [ %points. [ $+ [ $chan ] $+ ] .points [ $+ [ %line ] ] ] , %points, %name_number, 32)
            msg # $4 point(s) have been added for $capital($3) $+ . $capital($3) now has %points points.
          }
          else { msg # $capital($nick) $+ , that's not a valid number. }
        }
        else { msg # $capital($nick) $+ , that's not a valid username. }
      }
    }
  }
  elseif (%points.status. [ $+ [ $chan ] ] == off) { return }
  elseif ($points.findname($chan, $nick)) {
    var %line = $points.findname($chan, $nick)
    var %name_number = $findtok( [ %points. [ $+ [ $chan ] $+ ] .names [ $+ [ %line ] ] ] , $nick, 1, 32)
    var %points = $gettok( [ %points. [ $+ [ $chan ] $+ ] .points [ $+ [ %line ] ] ] , %name_number, 32)
    var %rank = $points.findrank($chan, %points)
    var %time = $points.minstotime($gettok( [ %points. [ $+ [ $chan ] $+ ] .minutes [ $+ [ %line ] ] ] , %name_number, 32))
    msg # $capital($nick) $+ , you are rank %rank with %points points ( $+ %time $+ ).
  }
}

alias points {
  if (%points.status. [ $+ [ $1 ] ] == off) { .timerpoints [ $+ [ $1 ] ] off }
  var %url = https://api.twitch.tv/kraken/streams/ $+ $mid($1,2-)
  if ($json(%url,stream) == $null && $1 != #harmon758) { return }
  %url = https://tmi.twitch.tv/group/user/  $+ $mid($1,2-) $+ /chatters $+ ?client_id=***REMOVED***
  var %counter = 0
  while ($json(%url,chatters,moderators,%counter)) {
    var %name = $json(%url,chatters,moderators,%counter)
    $points.processname($1, %name)
    inc %counter
  }
  %counter = 0
  while ($json(%url,chatters,viewers,%counter)) {
    var %name = $json(%url,chatters,viewers,%counter)
    $points.processname($1, %name)
    inc %counter
  }
}

alias points.findname {
  var %lines = %points. [ $+ [ $1 ] $+ ] .lines
  var %counter = 1
  while (%counter <= %lines) {
    if ($findtok( [ %points. [ $+ [ $1 ] $+ ] .names [ $+ [ %counter ] ] ] , $2, 0, 32) == 1) { return %counter }
    inc %counter
  }
  return 0
}

alias points.processname {
  if ($points.findname($1, $2)) {
    var %line = $points.findname($1, $2)
    var %name_number = $findtok( [ %points. [ $+ [ $1 ] $+ ] .names [ $+ [ %line ] ] ] , $2, 1, 32)
    var %points = $gettok( [ %points. [ $+ [ $1 ] $+ ] .points [ $+ [ %line ] ] ] , %name_number, 32)
    inc %points
    set %points. $+ $1 $+ .points $+ %line $puttok( [ %points. [ $+ [ $1 ] $+ ] .points [ $+ [ %line ] ] ] , %points, %name_number, 32)
    var %minutes = $gettok( [ %points. [ $+ [ $1 ] $+ ] .minutes [ $+ [ %line ] ] ] , %name_number, 32)
    inc %minutes
    set %points. $+ $1 $+ .minutes $+ %line $puttok( [ %points. [ $+ [ $1 ] $+ ] .minutes [ $+ [ %line ] ] ] , %minutes, %name_number, 32)
  }
  else {
    if ($len( [ %points. [ $+ [ $1 ] $+ ] .names [ $+ [ %points. [ $+ [ $1 ] $+ ] .lines ] ] ] ) > 4110) { inc %points. [ $+ [ $1 ] $+ ] .lines }
    var %line = %points. [ $+ [ $1 ] $+ ] .lines
    set %points. $+ $1 $+ .names $+ %line %points. [ $+ [ $1 ] $+ ] .names [ $+ [ %line ] ] $2
    set %points. $+ $1 $+ .points $+ %line %points. [ $+ [ $1 ] $+ ] .points [ $+ [ %line ] ] 1
    set %points. $+ $1 $+ .minutes $+ %line %points. [ $+ [ $1 ] $+ ] .minutes [ $+ [ %line ] ] 1
  }
}

alias points.writefiles {
  var %lines = %points. [ $+ [ $1 ] $+ ] .lines
  var %counter = 1
  write -c points. [ $+ [ $1 ] $+ ] .txt
  write -c points. [ $+ [ $1 ] $+ ] .sorted.txt
  while (%counter <= %lines) {
    var %numberofpoints = $numtok( [ %points. [ $+ [ $1 ] $+ ] .points [ $+ [ %counter ] ] ] , 32)
    var %counter2 = 1
    while (%counter2 <= %numberofpoints) {
      write points. [ $+ [ $1 ] $+ ] .txt  $gettok( [ %points. [ $+ [ $1 ] $+ ] .points [ $+ [ %counter ] ] ] , %counter2, 32)
      inc %counter2
    }
    inc %counter
  }
  filter -ffcute 1 32 points. [ $+ [ $1 ] $+ ] .txt points. [ $+ [ $1 ] $+ ] .sorted.txt
}

alias points.findrank {
  $points.writefiles($1)
  noop $read(points. [ $+ [ $1 ] $+ ] .sorted.txt, nst, $2)
  if ($readn) { return $readn }
  else { return -1 }
}

alias points.minstotime {
  var %mins = $1
  var %time
  if (%mins >= 525600) {
    %time = $floor($calc(%mins / 525600)) $+ y
    %mins = %mins % 525600
  }
  if (%mins >= 10080) {
    %time = %time $floor($calc(%mins / 10080)) $+ w
    %mins = %mins % 10080
  }
  if (%mins >= 1440) {
    %time = %time $floor($calc(%mins / 1440)) $+ d
    %mins = %mins % 1440
  }
  if (%mins >= 60) {
    %time = %time $floor($calc(%mins / 60)) $+ h
    %mins = %mins % 60
  }
  if (%mins > 0) {
    %time = %time %mins $+ m
  }
  return %time
}

;* /set: line too long (line 131, points)

on *:text:!ptesting*:#:{  }
