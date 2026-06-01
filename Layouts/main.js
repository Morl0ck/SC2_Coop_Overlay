var masteryNames = {
    'Abathur': ['Toxic Nest Damage', 'Mend Healing Duration', 'Symbiote Ability Improvement', 'Double Biomass Chance', 'Toxic Nest Maximum Charges and Cooldown', 'Structure Morph and Evolution Rate'],
    'Alarak': ['Alarak Attack Damage', 'Combat Unit Attack Speed', 'Empower Me Duration', 'Death Fleet Cooldown', 'Structure Overcharge Shield and Attack Speed', 'Chrono Boost Efficiency'],
    'Artanis': ['Shield Overcharge Duration and Damage Absorption', 'Guardian Shell Life and Shield Restoration', 'Energy Regeneration and Cooldown Reduction', 'Speed Increases for Warped In Units', 'Chrono Boost Efficiency', 'Initial and Maximum Spear of Adun Energy'],
    'Dehaka': ['Devour Healing Increase', 'Devour Buff Duration', 'Greater Primal Wurm Cooldown', 'Pack Leaders Active Duration', 'Gene Mutation Chance', 'Dehaka Attack Speed'],
    'Fenix': ['Fenix Suit Attack Speed', 'Fenix Suit Offline Energy Regeneration', 'Champion A.I. Attack Speed', 'Champion A.I. Life and Shields', 'Chrono Boost Efficiency', 'Extra Starting Supply'],
    'Horner': ['Strike Fighter Area of Effect', 'Stronger Death Chance', 'Significant Other Bonuses', 'Double Salvage Chance', 'Air Fleet Travel Distance', 'Mag Mine Charges, Cooldown, and Arming Time'],
    'Karax': ['Combat Unit Life and Shield', 'Structure Life and Shields', 'Repair Beam Healing Rate', 'Chrono Wave Energy Generation', 'Chrono Boost Efficiency', 'Initial and Maximum Spear of Adun Energy'],
    'Kerrigan': ['Kerrigan Energy Regeneration', 'Kerrigan Attack Damage', 'Combat Unit Vespene Gas Cost', 'Augmented Immobilization Wave', 'Expeditious Evolutions', 'Primary Ability Damage and Attack Speed'],
    'Nova': ['Nuke and Holo Decoy Cooldown', 'Griffin Airstrike Cost', 'Nova Primary Ability Improvement', 'Combat Unit Attack Speed', 'Nova Energy Regeneration', 'Unit Life Regeneration'],
    'Raynor': ['Research Resource Cost', 'Speed Increases for Drop Pod Units', 'Hyperion Cooldown', 'Banshee Airstrike Cooldown', 'Medics Heal Additional Target', 'Mech Attack Speed'],
    'Stetmann': ['Upgrade Resource Cost', 'Gary Ability Cooldown', 'Stetzone Bonuses', 'Maximum Egonergy Pool', 'Deploy Stetellite Cooldown', 'Structure Morph Rate'],
    'Stukov': ['Volatile Infested Spawn Chance', 'Infest Structure Cooldown', 'Aleksander Cooldown', 'Apocalisk Cooldown', 'Infested Infantry Duration', 'Mech Attack Speed'],
    'Swann': ['Concentrated Beam Width and Damage', 'Combat Drop Duration and Life', 'Immortality Protocol Cost and Build Time', 'Structure Health', 'Vespene Drone Cost', 'Laser Drill Build Time, Upgrade Time, and Upgrade Cost'],
    'Tychus': ['Tychus Attack Speed', 'Tychus Shredder Grenade Cooldown', 'Tri-Outlaw Research Improvement', 'Outlaw Availability', 'Medivac Pickup Cooldown', 'Odin Cooldown'],
    'Vorazun': ['Dark Pylon Range', 'Black Hole Duration', 'Shadow Guard Duration', 'Time Stop Unit Speed Increase', 'Chrono Boost Efficiency', 'Initial and Maximum Spear of Adun Energy'],
    'Zagara': ['Zagara And Queen Regen', 'Zagara Attack Damage', 'Intensified Frenzy', 'Zergling Evasion', 'Roach Damage and Life', 'Baneling Attack Damage'],
    'Zeratul': ['Zeratul Attack Speed', 'Combat Unit Attack Speed', 'Artifact Fragment Spawn Rate', 'Support Calldown Cooldown Reduction', 'Legendary Legion Cost', 'Avatar Cooldown'],
    'Mengsk': ['Laborer and Trooper Imperial Support', 'Royal Guard Support', 'Terrible Damage', 'Royal Guard Cost  ', 'Starting Imperial Mandate', 'Royal Guard Experience Gain Rate']
};

bonus_numbers = {
    'Chain of Ascension': 2,
    'Cradle of Death': 2,
    'Dead of Night': 1,
    'Lock & Load': 1,
    'Malwarfare': 2,
    'Miner Evacuation': 2,
    'Mist Opportunities': 2,
    'Oblivion Express': 2,
    'Part and Parcel': 2,
    'Rifts to Korhal': 2,
    'Scythe of Amon': 3,
    'Temple of the Past': 3,
    'The Vermillion Problem': 1,
    'Void Launch': 3,
    'Void Thrashing': 1
};

var showmutators = true;
var function_is_running = false;
var PORT = 7305;
var DURATION = 60;
var maxUnits = 5;
var gP1Color = '#0080F8';
var gP2Color = '#00D532';
var gP3Color = 'red';
var toBeShown = false;
var winrateTime = 12;
var showingWinrateStats = false;
var last_shown_file = '';
var do_not_use_websocket = false;
var minimum_kills = 1; // minimum number of kills for a unit to be shown
var show_charts = {};
var show_player_total_kills = false;
var func_on_new_data = null;

//main functionality
setColors(null, null, null, null);
setTimeout(function () {
    connect_to_socket();
    document.getElementById('bgdiv').style.display = 'block';
    document.getElementById('ibgdiv').style.display = 'block';
}, 500);


function connect_to_socket() {
    if (function_is_running) return;
    if (do_not_use_websocket) return;

    function_is_running = true;
    let socket = new WebSocket("ws://localhost:" + PORT);
    socket.onopen = function (e) { };
    socket.onmessage = function (event) {
        if (do_not_use_websocket) {
            socket.onclose = function () { };
            socket.close();
            return
        };
        let data = JSON.parse(event.data);
        if (data == null) return;
        console.log('New event');
        if (data['replaydata'] != null) {
            postGameStatsTimed(data)
        } else if (data['mutatordata'] != null) {
            mutatorInfo(data['data'])
        } else if (data['hideEvent'] != null) {
            hidestats()
        } else if (data['showEvent'] != null) {
            showstats()
        } else if (data['showHideEvent'] != null) {
            showhide()
        } else if (data['uploadEvent'] != null) {
            setTimeout(uploadStatus, 1500, data['response'])
        } else if (data['initEvent'] != null) {
            initColorsDuration(data)
        } else if (data['playerEvent'] != null) {
            showHidePlayerWinrate(data)
        } else if (data['missionStartEvent'] != null) {
            missionStart(data)
        } else if (data['missionTimeEvent'] != null) {
            missionSyncTime(data)
        } else if (data['missionEndEvent'] != null) {
            missionEnd()
        } else {
            console.log('unidentified message')
        }
    };

    socket.onclose = function (event) {
        if (event.wasClean) console.log('CLEAN EXIT: ' + event);
        else console.log('UNCLEAN EXIT: ' + event);
        reconnect_to_socket();
    };

    socket.onerror = function (error) {
        console.log('ERROR: ' + error);
        reconnect_to_socket()
    };
}


function reconnect_to_socket(message) {
    console.log('Reconnecting..')
    function_is_running = false;
    setTimeout(function () {
        connect_to_socket();
    }, 1000);
}


function showHidePlayerWinrate(dat) {
    if (showingWinrateStats) {
        showingWinrateStats = false;
        document.getElementById('playerstats').style.right = '-60vh';
        document.getElementById('playerstats').style.opacity = '0';
    } else {
        playerWinrate(dat)
    }
}


function playerWinrate(dat) {
    let element = document.getElementById('playerstats');
    let text = '';
    showingWinrateStats = true;
    if (dat == null) return;

    for (let [key, value] of Object.entries(dat['data'])) {
        // no data ([None])
        if ((value.length == 1) && (value[0] == null)) {
            text += 'No games played with <span class="player_stat">' + key + '</span>'

            // no winrate data but with a player note ([None, note])
        } else if ((value.length == 2) && (value[0] == null)) {
            text += 'No games played with <span class="player_stat">' + key + '</span><br>' + value[1]

            // winrate data ([wins, losses, apm, commander, frequency, kills, date])
        } else if (value.length >= 7) {
            let total_games = value[0] + value[1];
            text += 'You played ' + total_games + ' games with <span class="player_stat">' + key + '</span>';
            text += ' (' + Math.round(100 * value[0] / total_games) + '% winrate | ' + Math.round(100 * value[5]) + '% kills | ' + value[2] + ' APM)<br>Last game played together: ' + value[6]
        }
        // winrate data and player note ([wins, losses, apm, commander, frequency, kills,  date, note])
        if (value.length == 8) {
            text += '<br>' + value[7]
        }
    }
    element.innerHTML = text;
    element.style.right = '2vh';
    element.style.opacity = '1';
    setTimeout(function () {
        document.getElementById('playerstats').style.right = '-60vh';
        document.getElementById('playerstats').style.opacity = '0';
        showingWinrateStats = false;
    }, winrateTime * 1000)
}

function initColorsDuration(data) {
    setColors(data['colors'][0], data['colors'][1], data['colors'][2], data['colors'][3]);
    DURATION = data['duration'];
    show_charts = data['charts']
    UpdateChartsVisibility();
    if (data['mission_overlay'] != null) applyMissionOverlaySettings(data['mission_overlay']);
    console.log('Received init data. Duration: ' + DURATION + 's. Show charts: ' + JSON.stringify(show_charts, null, 2));
}

function UpdateChartsVisibility() {
   document.getElementById('armyChart').style.display = show_charts['army'] ? 'block' : 'none';
   document.getElementById('supplyChart').style.display = show_charts['supply'] ? 'block' : 'none';
   document.getElementById('killedChart').style.display = show_charts['kills'] ? 'block' : 'none';
   document.getElementById('miningChart').style.display = show_charts['collection_rate'] ? 'block' : 'none';
   document.getElementById('mineralsChart').style.display = show_charts['minerals'] ? 'block' : 'none';
   document.getElementById('vespeneChart').style.display = show_charts['vespene'] ? 'block' : 'none';
   document.getElementById('resourcesChart').style.display = show_charts['resources'] ? 'block' : 'none';
} 

function setColors(P1color, P2color, P3color, MasteryColor) {
    //this function is executed by the app on page load
    //Player 1
    if (P1color != null) gP1Color = P1color;
    document.getElementById('name1').style.color = gP1Color;
    document.getElementById('CMname1').style.color = gP1Color;
    document.getElementById('killbar1').style.backgroundColor = gP1Color;
    document.getElementById('CMtalent1').style.color = gP1Color;

    //Player 2
    if (P2color != null) gP2Color = P2color;
    document.getElementById('name2').style.color = gP2Color;
    document.getElementById('CMname2').style.color = gP2Color;
    document.getElementById('killbar2').style.backgroundColor = gP2Color;
    document.getElementById('CMtalent2').style.color = gP2Color;

    //Player 3
    if (P3color != null) gP3Color = P3color;
    document.getElementById('CMname3').style.color = gP3Color;
    document.getElementById('comp').style.color = gP3Color;

    //Mastery
    let color = '#FFDC87';
    if (MasteryColor != null) color = MasteryColor;
    document.getElementById('CMmastery1').style.color = color;
    document.getElementById('CMmastery2').style.color = color;

    //Charts
    update_charts_colors(gP1Color, gP2Color)
}


function uploadStatus(result) {
    let loader = document.getElementById('loader');

    loader.style.transition = 'opacity 0s';
    loader.style.opacity = '0'
    loader.style.transition = 'opacity 1s';
    loader.innerHTML = ''
    loader.style.opacity = '1';

    if (result.includes('Success')) {
        loader.style.color = 'rgba(0, 150, 0, 1)';
        loader.innerHTML = 'Replay uploaded successfully!';
    } else {
        loader.style.color = 'rgba(225, 0, 0, 1)';
        loader.innerHTML = 'Replay not uploaded!<br>' + result;
    };
}


function mutatorInfo(data) {
    if (!(showmutators)) return;

    let mduration = 15 * 1000;
    if (data.length > 6) {
        document.getElementById('mutatorinfo').style.width = '133vh';
    }
    for (i = 0; i < data.length; i++) {
        var divelement = document.getElementById('mut' + i);
        divelement.getElementsByTagName("img")[0].src = '../HQ Mutator Icons/' + data[i][0] + '.png';
        divelement.getElementsByTagName("p")[0].innerHTML = '<span class="muttop">' + data[i][0] + '</span><span class="mutvalue"> ' + data[i][1] + '</span><br><span class="mutdesc">' + mutatorDescriptions[data[i][0]] + '</span>';
        divelement.style.display = 'inline-block';
        setTimeout(function (el) {
            el.style.opacity = '1'
        }, i * 400, divelement);
        setTimeout(function (el) {
            el.style.opacity = '0'
        }, mduration, divelement);
        setTimeout(function (el) {
            el.style.display = 'none'
        }, mduration + 5000, divelement);
    }
}


function postGameStatsTimed(data) {
    //This is a wrapper for postGameStats
    //The goal is to nicely update the data if it's already showing
    if ((document.getElementById('stats').style.right != '-50.5vh') && (document.getElementById('stats').style.right != '')) {

        // If we are about to show the same data, hide instead
        if (last_shown_file == data['file']) {
            hidestats()
        } else {
            document.getElementById('stats').style.opacity = '0';
            setTimeout(function () {
                document.getElementById('stats').style.opacity = '1'
            }, 300);
            setTimeout(postGameStats, 300, data, showing = true);
        }
    } else {
        postGameStats(data);
    }
}


function format_length(seconds, multiply = true) {
    let gseconds = 0;
    if (multiply) gseconds = Math.round(seconds * 1.4);
    else gseconds = Math.round(seconds);

    let sec = gseconds % 60;
    let min = ((gseconds - sec) / 60) % 60;
    let hr = (gseconds - sec - min * 60) / 3600;

    if (hr > 0) hr += ':';
    else hr = '';

    if (min == 0) min = '00:';
    else if (min < 10) min = '0' + min + ':';
    else min += ':';

    if (sec < 10) sec = '0' + sec;

    return hr + min + sec
}


function fillCommander(el, commander, commander_level) {
    let addition = '';
    if (commander == null) return;
    if (commander_level < 15) addition = '{' + commander_level + '}';
    if (el == 'com1') fill(el, commander + ' ' + addition);
    else fill(el, addition + ' ' + commander)
}


function postGameStats(data, showing = false) {
    //initial change
    document.getElementById('killbar').style.display = 'block';
    document.getElementById('nodata').style.display = 'none';
    //fill
    fill('CMtalent1', data['mainPrestige'])
    fill('CMtalent2', data['allyPrestige'])
    fill('comp', data['comp']);

    // update charts
    if (data['player_stats'] != null) plot_charts(data['player_stats']);

    // if there is an custom function declared 
    if (func_on_new_data != null) func_on_new_data(data);

    // save file name
    last_shown_file = data['file'];

    // Mutators
    let mutator_text = '';
    if ((data['mutators'] != null) && (data['mutators'].length > 0)) {
        for (i = 0; i < data['mutators'].length; i++) {
            mutator_text = mutator_text + '<img src="Mutator Icons/' + data['mutators'][i] + '.png">'
        }
        fill('mutators', mutator_text);
        fill('result', data['result'] + '!');
    } else {
        fill('mutators', '<span id="resultsp">' + data['result'] + '!</span>');
        fill('result', 'kills');
    }

    //BG images
    if ((data['mainCommander'] != null) && (data['mainCommander'] != '')) {
        document.getElementById('killbar1img').src = 'Commanders/' + data['mainCommander'] + '.png'
    } else {
        document.getElementById('killbar1img').src = ''
    }
    if ((data['allyCommander'] != null) && (data['allyCommander'] != '')) {
        document.getElementById('killbar2img').src = 'Commanders/' + data['allyCommander'] + '.png'
    } else {
        document.getElementById('killbar2img').src = ''
    }

    // Bonus objectives
    let bonus_text = '';
    if (data['map_name'] in bonus_numbers)
        bonus_text = `(${data['bonus'].length}/${bonus_numbers[data['map_name']]})`
    else
        bonus_text = `(${data['bonus'].length}/?)`
    bonus_text = ` <span style="color: #FFE670">${bonus_text}</span>`;

    fill('name1', data['main']);
    fill('map', `${data['map_name']}&nbsp;&nbsp;(${format_length(data['length'])}) ${bonus_text}`);
    fill('name2', data['ally']);
    fillCommander('com1', data['mainCommander'], data['mainCommanderLevel'])
    fillCommander('com2', data['allyCommander'], data['allyCommanderLevel'])
    fill('apm1', data['mainAPM'] + ' APM');
    fill('apm2', data['allyAPM'] + ' APM');

    if (data['fastest'] == true) {
        document.getElementById('record').style.display = 'block';
    } else {
        document.getElementById('record').style.display = 'none';
    }

    if (data['Victory'] != null) {
        fill('session', 'Session: ' + data['Victory'] + ' wins/' + (data['Victory'] + data['Defeat']) + ' games');
    } else {
        fill('session', '');
    };

    if (data['Commander'] != null) {
        fill('rng', 'Randomized commander: ' + data['Commander'] + ' (' + data['Prestige'] + ')');
    } else {
        fill('rng', '');
    };

    // difficulty
    if ((data['weekly'] == true)) {
        fill('brutal', 'Weekly (' + data['difficulty'] + ')')
    } else if ((data['extension'] > 0) && (data['mutators'] != null)) {
        fill('brutal', 'Custom (' + data['difficulty'] + ')')
    } else if (data['B+'] > 0) {
        fill('brutal', 'Brutal+' + data['B+'])
    } else {
        fill('brutal', data['difficulty'])
    };

    // kill counts
    let totalkills = data['mainkills'] + data['allykills']
    if (totalkills > 0) {
        var percent1 = Math.round(100 * data['mainkills'] / totalkills) + '%';
        var percent2 = Math.round(100 * data['allykills'] / totalkills) + '%';
        document.getElementById('killbar1').style.backgroundColor = gP1Color;
        document.getElementById('killbar2').style.backgroundColor = gP2Color;
        //delay unless it's already being showed
        if (!(showing)) {
            setTimeout(function () {
                document.getElementById('killbar1').style.width = percent1;
                document.getElementById('killbar2').style.width = percent2;
            }, 700)
        } else {
            document.getElementById('killbar1').style.width = percent1;
            document.getElementById('killbar2').style.width = percent2
        };
        if (show_player_total_kills) {
            fill('percent1', `${percent1} (${data['mainkills']})`);
            fill('percent2', `${percent2} (${data['allykills']})`);
        } else {
            fill('percent1', percent1);
            fill('percent2', percent2);
        }

    } else {
        document.getElementById('killbar1').style.width = '50%';
        document.getElementById('killbar2').style.width = '50%';
        document.getElementById('killbar1').style.backgroundColor = '#666';
        document.getElementById('killbar2').style.backgroundColor = '#444';
        fill('percent1', '0%');
        fill('percent2', '0%');
    };

    //player stats
    fill('CMname1', data['main']);
    fillicons('CMicons1', data['mainIcons']);
    fillmasteries('CMmastery1', data['mainMasteries'], data['mainCommander']);
    fillunits('CMunits1', data['mainUnits'], data['mainCommander'], gP1Color, totalkills);

    fill('CMname2', data['ally']);
    fillicons('CMicons2', data['allyIcons']);
    fillmasteries('CMmastery2', data['allyMasteries'], data['allyCommander']);
    fillunits('CMunits2', data['allyUnits'], data['allyCommander'], gP2Color, totalkills);

    fill('CMname3', 'Amon');
    fillunits('CMunits3', data['amon_units'], null, 'red', totalkills);

    // add a tiny delay before updating. This can smooth out things on some systems.
    setTimeout(showstats, 10);

    //victory data is for automatic showing. In that case automatically hide. Otherwise hide loader.
    if (data['Victory'] == null) {
        document.getElementById('loader').style.opacity = '0';
        document.getElementById('loader').innerHTML = ''
    }
    if (data['newReplay'] != null) {
        setTimeout(hidestats, DURATION * 1000);
    }
}


function showhide() {
    console.log('showhide()');
    if (!toBeShown) showstats();
    else hidestats()
}


function showhide_charts(show) {
    console.log('showhide_charts(' + show + ')');
    // updates visibility and future showing
    if (show) {
        if (toBeShown) document.getElementById('charts').style.opacity = '1';
        document.getElementById('bgdiv').style.width = '100vh';
        show_charts = true
    } else {
        document.getElementById('charts').style.opacity = '0';
        document.getElementById('bgdiv').style.width = '65vh';
        show_charts = false
    }
}


function hidestats() {
    toBeShown = false;
    document.getElementById('stats').style.right = '-50.5vh';
    document.getElementById('bgdiv').style.opacity = '0';
    document.getElementById('loader').style.opacity = '0';
    document.getElementById('session').style.opacity = '0';
    document.getElementById('rng').style.opacity = '0';
    document.getElementById('charts').style.opacity = '0';
    setTimeout(function () {
        document.getElementById('session').innerHTML = '';
        document.getElementById('rng').innerHTML = '';
        document.getElementById('loader').style.opacity = '0';
        document.getElementById('loader').innerHTML = ''
    }, 1000)
}


function showstats() {
    toBeShown = true;
    document.getElementById('stats').style.right = '1vh';
    document.getElementById('bgdiv').style.opacity = '1';
    if (show_charts) document.getElementById('charts').style.opacity = '1';
    setTimeout(function () { document.getElementById('session').style.opacity = '0.6'; document.getElementById('rng').style.opacity = '1' }, 1000)
}

function fill(el, dat) {
    document.getElementById(el).innerHTML = dat;
}

function fillmasteries(el, dat, commander) {
    let text = '';
    if ((dat == null) || (commander == null) || (commander == '') || (masteryNames[commander] == null)) {
        document.getElementById(el).innerHTML = '';
        return
    };
    let any_mastery = false;
    for (i = 0; i < dat.length; i++) {
        let spacer = '<span>';
        if (dat[i] < 10) spacer = '<span class="singlemastery">';
        if (dat[i] == 0) spacer = '<span class="nomastery">';
        else any_mastery = true;
        text += spacer + dat[i] + ' ' + masteryNames[commander][i] + '<br></span>';
    }
    if (any_mastery) document.getElementById(el).style.display = 'block';
    else document.getElementById(el).style.display = 'none';

    document.getElementById(el).innerHTML = text;
}


function fillicons(el, data) {
    let text = '';
    for (let [key, value] of Object.entries(data)) {
        if (key == 'outlaws') {
            for (i = 0; i < data['outlaws'].length; i++) {
                text = text + '<img src="Icons/' + data['outlaws'][i] + '.png">';
            }

        } else if ((['hfts', 'tus', 'propagators', 'voidrifts', 'turkey', 'voidreanimators', 'deadofnight', 'minesweeper', 'missilecommand'].includes(key)) && (value > 0)) {
            text = text + '<img src="Icons/' + key + '.png"> <span class="icontext">' + value + '</span>';

        } else if ((key == 'killbots') && (value > 0)) {
            text = text + '<img src="Icons/' + key + '.png"> <span class="icontext killbotkills">-' + value + '</span>';

        } else if (value > 0) {
            text = text + '<img src="Icons/' + key + '.png"> <span class="icontext iconcreated">+' + value + '</span>';
        }
    }
    document.getElementById(el).innerHTML = text
}


function fillunits(el, dat, commander, color, total_kills = null) {
    let text = '<span class="unitkills">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;kills</span><span class="unitcreated header">created</span><span class="unitdied header">lost</span><br>';
    let percent = 0;
    let spacer = '';
    let idx = 0;

    if (dat == null) return;

    for (let [key, value] of Object.entries(dat)) {
        if (idx === maxUnits) break;

        // Switch few unit names
        if ((key == 'Stalker') && (commander == 'Alarak')) key = 'Slayer';
        if ((key == 'Sentinel') && (commander == 'Fenix')) key = 'Legionnaire';

        spacer = '';
        percent = Math.round(100 * value[3]);
        if (percent < 10) spacer = 'killpadding';
        else if (percent == 100) spacer = 'nokillpadding';
        if (value[2] >= minimum_kills) {
            idx += 1;
            if (total_kills != null && total_kills > 0) bg_width = 50 * value[2] / total_kills;
            else bg_width = 35 * percent / 100;

            text += '<div class="unitkillbg" style="width: ' + bg_width + 'vh; background-color: ' + color + '"></div><div class="unitline">' + key + ' <span class="unitkills ' + spacer + '">' + percent + '% | ' + value[2] + '</span>  <span class="unitcreated">' + value[0] + '</span>  <span class="unitdied">' + value[1] + '</span><div>'
        };
    }

    if (idx == 0) text = '<span class="unitkills"></span>';
    document.getElementById(el).innerHTML = text;
}


// ---------------------------------------------------------------------------
// Mission "what's next" overlay
//
// Python sends sparse events (start / time-sync / end). The countdown itself
// runs locally here so we never depend on per-second traffic from Python.
// ---------------------------------------------------------------------------
var missionEvents = [];          // pre-sorted list of {time, kind, label, ...}
var missionMapName = '';
var missionHasPatterns = false;
var missionSyncedTime = 0;       // last displayTime received from SC2 (game-clock seconds)
var missionSyncWall = 0;         // Date.now() when missionSyncedTime was set
var missionSpeed = 1.4;          // game-clock seconds per wall second (Faster = ~1.4)
var missionPaused = false;
var missionInterval = null;
var missionLastNextStr = null;
var missionLastUpcomingStr = null;
var missionLastNameStr = null;
var missionLastPrevStr = null;
var missionUpcomingLimit = 3;
var missionVisible = false;
var missionCfg = {
    anchor_h: 'left', anchor_v: 'bottom',
    offset_x: 2, offset_y: 27,
    opacity: 0.9,
    show_previous: true, show_next: true,
    font_next: 1.55, font_other: 1.2
};


function applyMissionOverlaySettings(cfg) {
    // Merge incoming config and apply position / opacity / fonts / visibility.
    if (cfg != null) {
        for (let k in cfg) missionCfg[k] = cfg[k];
    }
    let panel = document.getElementById('missioninfo');

    // Position (anchor to a corner with an offset, in vh)
    panel.style.top = 'auto';
    panel.style.bottom = 'auto';
    panel.style.left = 'auto';
    panel.style.right = 'auto';
    if (missionCfg.anchor_h === 'right') panel.style.right = missionCfg.offset_x + 'vh';
    else panel.style.left = missionCfg.offset_x + 'vh';
    if (missionCfg.anchor_v === 'top') panel.style.top = missionCfg.offset_y + 'vh';
    else panel.style.bottom = missionCfg.offset_y + 'vh';

    // Font sizes
    document.getElementById('missionnext').style.fontSize = missionCfg.font_next + 'vh';
    document.getElementById('missionname').style.fontSize = missionCfg.font_other + 'vh';
    document.getElementById('missionprev').style.fontSize = missionCfg.font_other + 'vh';
    document.getElementById('missionupcoming').style.fontSize = missionCfg.font_other + 'vh';

    // Section visibility
    document.getElementById('missionprev').style.display = missionCfg.show_previous ? 'block' : 'none';
    document.getElementById('missionnext').style.display = missionCfg.show_next ? 'block' : 'none';
    document.getElementById('missionupcoming').style.display = missionCfg.show_next ? 'block' : 'none';

    // Live opacity update while shown
    if (missionVisible) panel.style.opacity = missionCfg.opacity;
}

function missionStart(data) {
    if (data == null || data['events'] == null) return;
    missionEvents = data['events'].slice().sort(function (a, b) { return a.time - b.time; });
    missionMapName = data['map_name'] || '';
    missionHasPatterns = missionEvents.some(function (e) { return e.pattern != null; });
    missionSyncedTime = data['displayTime'] || 0;
    missionSyncWall = Date.now();
    missionSpeed = 1.4;
    missionPaused = false;
    missionLastNextStr = null;
    missionLastUpcomingStr = null;
    missionLastNameStr = null;
    missionLastPrevStr = null;

    missionVisible = true;
    applyMissionOverlaySettings(null);  // re-apply current position / fonts / visibility
    let panel = document.getElementById('missioninfo');
    panel.style.opacity = missionCfg.opacity;

    renderMissionPanel();
    if (missionInterval == null) {
        missionInterval = setInterval(renderMissionPanel, 1000);
    }
    console.log('Mission started: ' + missionMapName);
}


function missionSyncTime(data) {
    if (data == null || data['displayTime'] == null) return;
    let newTime = data['displayTime'];
    let now = Date.now();
    let wallDelta = (now - missionSyncWall) / 1000;

    // Same clock value across two syncs => the game is paused.
    if (newTime === missionSyncedTime) {
        missionPaused = true;
    } else {
        // Estimate the game-clock speed from the observed delta (Faster ~1.4),
        // clamped to a sane range so a stray sample can't break the countdown.
        if (wallDelta > 0.5) {
            let observed = (newTime - missionSyncedTime) / wallDelta;
            if (observed > 0.5 && observed < 3) missionSpeed = observed;
        }
        missionPaused = false;
    }
    missionSyncedTime = newTime;
    missionSyncWall = now;
    renderMissionPanel();
}


function missionEnd() {
    if (missionInterval != null) {
        clearInterval(missionInterval);
        missionInterval = null;
    }
    missionEvents = [];
    missionMapName = '';
    missionVisible = false;
    document.getElementById('missioninfo').style.opacity = '0';
    console.log('Mission ended');
}


function missionCurrentTime() {
    // Interpolate the in-game clock between syncs.
    if (missionPaused) return missionSyncedTime;
    let wallDelta = (Date.now() - missionSyncWall) / 1000;
    return missionSyncedTime + wallDelta * missionSpeed;
}


function missionFormatCountdown(seconds) {
    if (seconds < 0) seconds = 0;
    seconds = Math.round(seconds);
    let sec = seconds % 60;
    let min = (seconds - sec) / 60;
    if (sec < 10) sec = '0' + sec;
    return min + ':' + sec;
}


function getUpcomingEvents(gameTime, events, limit) {
    // Future events only, already time-sorted. Pattern A/B entries are both
    // kept so the panel shows every possible "next" until the game resolves it.
    let upcoming = [];
    for (let i = 0; i < events.length; i++) {
        if (events[i].time > gameTime) {
            upcoming.push(events[i]);
            if (upcoming.length >= limit) break;
        }
    }
    return upcoming;
}


function getPreviousEvent(gameTime, events) {
    // Most recent event that has already happened (events are time-sorted).
    let prev = null;
    for (let i = 0; i < events.length; i++) {
        if (events[i].time <= gameTime) prev = events[i];
        else break;
    }
    return prev;
}


function missionEventText(ev, gameTime, past) {
    let delta = past ? (gameTime - ev.time) : (ev.time - gameTime);
    let timeStr = missionFormatCountdown(delta) + (past ? ' ago' : '');
    let cls = ev.kind === 'attack_wave' ? 'mission-wave' : 'mission-objective';
    let label = ev.label || (ev.kind === 'attack_wave' ? 'Attack wave' : 'Event');
    if (ev.pattern != null) label += ' [' + ev.pattern + ']';

    let detail = '';
    let parts = [];
    if (ev.tech != null && ev.strength != null) parts.push('T' + ev.tech + '/S' + ev.strength);
    if (ev.spawn != null) parts.push(ev.spawn);
    if (parts.length > 0) detail = ' <span class="mission-detail">(' + parts.join(', ') + ')</span>';

    return '<span class="' + cls + '">' + label + '</span> <span class="mission-countdown">' + timeStr + '</span>' + detail;
}


function renderMissionPanel() {
    if (missionEvents.length === 0) return;
    let gameTime = missionCurrentTime();
    let upcoming = getUpcomingEvents(gameTime, missionEvents, missionUpcomingLimit);

    // Map name (+ Brutal-timings note)
    let nameStr = missionMapName + ' <span class="mission-detail">(Brutal)</span>';
    if (nameStr !== missionLastNameStr) {
        document.getElementById('missionname').innerHTML = nameStr;
        missionLastNameStr = nameStr;
    }

    // PREVIOUS line
    let prev = getPreviousEvent(gameTime, missionEvents);
    let prevStr = prev ? '<span class="mission-label">PREV:</span> ' + missionEventText(prev, gameTime, true) : '';
    if (prevStr !== missionLastPrevStr) {
        document.getElementById('missionprev').innerHTML = prevStr;
        missionLastPrevStr = prevStr;
    }

    // NEXT line
    let nextStr;
    if (upcoming.length > 0) {
        nextStr = '<span class="mission-label">NEXT:</span> ' + missionEventText(upcoming[0], gameTime);
    } else {
        nextStr = '<span class="mission-label">No further events</span>';
    }
    if (nextStr !== missionLastNextStr) {
        document.getElementById('missionnext').innerHTML = nextStr;
        missionLastNextStr = nextStr;
    }

    // Following lines
    let upcomingStr = '';
    for (let i = 1; i < upcoming.length; i++) {
        upcomingStr += '<span class="mission-label">THEN:</span> ' + missionEventText(upcoming[i], gameTime) + '<br>';
    }
    if (upcomingStr !== missionLastUpcomingStr) {
        document.getElementById('missionupcoming').innerHTML = upcomingStr;
        missionLastUpcomingStr = upcomingStr;
    }
}