set TARGET_APOAPSIS to 200000. 
set MUN_ALT to 11400000.

function ForceStage {
    print ">>> СБРОС СТУПЕНИ <<<" at (0,0).
    lock throttle to 0. 
    wait 1. 
    stage. 
    wait 5.
}

function WaitBeforeStart {
    clearscreen.
    set timer to 5.
    until timer = 0 { print "Старт: " + timer at (0,0). set timer to timer - 1. wait 1. }
    print "ПОЕХАЛИ!". wait 1.
}

function Phase1_Ascent {
    clearscreen.
    print "ЭТАП 1".
    sas off.
    lock throttle to 1.
    stage. wait 2.
    set max_thrust_start to ship:maxthrust.

    until ship:maxthrust < (max_thrust_start * 0.85) {
        
        if ship:altitude < 20000 {
            lock steering to heading(90, 90 - 30 * (ship:altitude / 20000)).
        } 
        else if ship:altitude < 30000 {
            lock steering to heading(90, 60 - 15 * ((ship:altitude - 20000) / 10000)).
        }
        else {
            lock steering to heading(90, 45).
        }
        
        print "Высота: " + round(ship:altitude) at (0,5).
        print "Угол:   " + round(90 - vang(ship:up:vector, ship:facing:vector)) at (0,6).
        wait 0.1.
    }

    print "СБРОС.".
    stage. wait 2.
}

function Phase2_Center {
    clearscreen.
    print "ЭТАП 2: ЦЕНТРАЛЬНАЯ СТУПЕНЬ".
    
    lock steering to heading(90, 20).
    lock throttle to 1.

    wait until ship:altitude > 70000.
    print "Космос. Сброс обтекателя.".
    
    lock steering to "kill". 
    wait 0.5.
    stage. 
    wait 2.
    lock steering to heading(90, 20). 
    // -------------------------------------

    until ship:apoapsis > TARGET_APOAPSIS {
        print "Апоцентр: " + round(ship:apoapsis) at (0,5).
        if ship:maxthrust < 0.1 { break. }
    }

    print "Апоцентр 200км достигнут. СБРОС СТУПЕНИ.".
    ForceStage(). 
}

function Phase3_Orbit {
    clearscreen.
    print "ЭТАП 3: ОЖИДАНИЕ АПОЦЕНТРА".
    
    lock steering to heading(90, 0).
    lock throttle to 0.

    if eta:apoapsis > 40 {
        set kuniverse:timewarp:mode to "RAILS".
        set kuniverse:timewarp:warp to 3.
        wait until eta:apoapsis < 30.
        set kuniverse:timewarp:warp to 0.
    }
    
    wait until eta:apoapsis < 20.
    
    lock throttle to 1.
    
    until ship:periapsis > (TARGET_APOAPSIS - 5000) {
        print "Перицентр: " + round(ship:periapsis) at (0,5).
        if ship:maxthrust < 0.1 { stage. wait 1. }
    }
    
    print "Орбита готова. СБРОС СТУПЕНИ.".
    ForceStage().
}

function Phase4_Transfer {
    clearscreen.
    print "ЭТАП 4: ПОИСК ОКНА".
    
    lock throttle to 0.
    wait until CheckCanGoToMoon().
    
    lock steering to prograde.
    wait 5.
    lock throttle to 1.
    
    until orbit:apoapsis > MUN_ALT {
         if ship:maxthrust < 0.1 { stage. wait 1. }
    }
    
    print "Траектория построена. ТЯГА 0.".
    lock throttle to 0.
}

function Phase5_Landing {
    clearscreen.
    
    set kuniverse:timewarp:mode to "RAILS".
    set kuniverse:timewarp:warp to 4.
    
    wait until ship:body:name = "Mun".
    set kuniverse:timewarp:warp to 0. wait 5.
    
    print "Вход в SOI Муны.".
    ForceStage(). 
    
    lock throttle to 0.
    
    print "Падение до 100 км...".
    if ship:altitude > 100000 {
        set kuniverse:timewarp:warp to 3.
        wait until ship:altitude < 110000.
        set kuniverse:timewarp:warp to 0.
        wait until ship:altitude < 100000.
    }
    
    print "НАЧИНАЕМ ПОСАДКУ (100 КМ)".
    
    lock steering to srfretrograde.
    legs on.
    lights on.
    
    print "Гашение орбитальной скорости...".
    lock throttle to 0.5.
    wait until ship:groundspeed < 50. 
    lock throttle to 0.
    
    
    until ship:status = "LANDED" or ship:status = "SPLASHED" {
        set val to FindX().
        lock throttle to val.
        if ship:maxthrust < 0.1 { stage. wait 0.5. }
        wait 0.1.
    }
    
    lock throttle to 0. unlock steering.
    print "УСПЕШНАЯ ПОСАДКА!".
}

function CheckCanGoToMoon {
    set Vector_Kerbin_Mun to body("Mun"):position - body("Kerbin"):position.
    set Vector_Kerbin_ship to Ship:position - body("Kerbin"):position.
    set angle_ship_Moon to VANG(Vector_Kerbin_Mun, Vector_Kerbin_ship).
    if (VANG(VXCL(ship:up:vector, ship:velocity:orbit), body("Mun"):position - ship:position) > 90) {
		set angle_ship_Moon to -angle_ship_Moon.
	}
    set a1 to (Vector_Kerbin_Mun:mag + ship:altitude + body("Kerbin"):radius) / 2.
	set a2 to Vector_Kerbin_Mun:mag.
	set angle_true to 180 * (1 - (a1/a2) ^ 1.5).
    
    clearscreen.
    print "Угол: " + round(angle_ship_Moon) + " / " + round(angle_true).
    return abs(angle_ship_Moon - angle_true) < 3.
}

function FindX {
    if ship:maxthrust < 0.001 { return 1. } 
    set b1 to ship:mass / ship:maxthrust.
    set b2 to (ship:velocity:surface:mag ^ 2) / (2 * ship:bounds:bottomaltradar).
    set g to (6.67 * (10 ^ (-11))) * ((9.76 * (10 ^ 20)) / ((200000 + ship:bounds:bottomaltradar) ^ 2)).
    set true_force to b1 * (b2 + g).
    set work_force to true_force.
    if true_force > 0.5 { set work_force to 0.5 + (true_force - 0.5) * 3. }
    if work_force > 1 { set work_force to 1. }
    
    clearscreen.
    print "СКОРОСТЬ: " + round(ship:velocity:surface:mag) + " м/с".
    print "ВЫСОТА:   " + round(ship:bounds:bottomaltradar) + " м".
    print "ТЯГА:     " + round(work_force * 100) + "%".
    
    return work_force.
}

WaitBeforeStart().
Phase1_Ascent().
Phase2_Center().
Phase3_Orbit().
Phase4_Transfer().
Phase5_Landing().
