% ============================================================================
% HARRIET'S WORLD - NARRATIVE LAYER
% Memory plague, dialogue fingerprints, endings, and story content
% ============================================================================
% Requires: harriets_world_kernel_002.pl, epistemics.pl
% ============================================================================

% ============================================================================
% SECTION 26: MEMORY PLAGUE MODEL
% ============================================================================

plague(memory_plague).
symptom(memory_plague, headache).
symptom(memory_plague, hallucination).
symptom(memory_plague, identity_confusion).
symptom(memory_plague, false_memories).
symptom(memory_plague, identity_bleed).
symptom(memory_plague, delirium_euphoria).
symptom(memory_plague, deja_vu).

wave(memory_plague_wave_1).
instance_of(memory_plague_wave_1, memory_plague).
origin_location(memory_plague_wave_1, vending_row).
origin_carrier(memory_plague_wave_1, work_dog_funks).

% Epidemic timeline
time(t_plague_start).
time(t_plague_peak).
time(t_plague_recession).
time(t_plague_day_1).
time(t_plague_day_3).
time(t_plague_day_7).
time(t_plague_day_14).
time(t_plague_day_21).

before(t_plague_start, t_plague_peak).
before(t_plague_peak, t_plague_recession).
before(t_plague_day_1, t_plague_day_3).
before(t_plague_day_3, t_plague_day_7).
before(t_plague_day_7, t_plague_day_14).
before(t_plague_day_14, t_plague_day_21).
before(t_plague_start, t_plague_day_1).
before(t_plague_day_21, t_plague_peak).

channel(proximity).
channel(network).

% Exposures
exposure(memory_plague_wave_1, vending_row, work_dog_funks, proximity, t_plague_start).
exposure(memory_plague_wave_1, work_dog_funks, bobs_oasis_regulars, proximity, t_plague_start).
exposure(memory_plague_wave_1, bobs_oasis_regulars, gallup_locals, proximity, t_plague_peak).
exposure(memory_plague_wave_1, vending_row, scraps, proximity, t_plague_day_1).
exposure(memory_plague_wave_1, scraps, dinger, proximity, t_plague_day_3).
exposure(memory_plague_wave_1, scraps, eddie, proximity, t_plague_day_3).
exposure(memory_plague_wave_1, dinger, vinnie, proximity, t_plague_day_7).
exposure(memory_plague_wave_1, eddie, bob, proximity, t_plague_day_7).
exposure(memory_plague_wave_1, eddie, whirly, proximity, t_plague_day_7).
exposure(memory_plague_wave_1, vinnie, clank, proximity, t_plague_day_14).
exposure(memory_plague_wave_1, bob, harriet_holloway, proximity, t_plague_day_14).

% Infection events
happens(infected(memory_plague_wave_1, work_dog_funks), t_plague_start).
happens(infected(memory_plague_wave_1, bobs_oasis_regulars), t_plague_start).
happens(infected(memory_plague_wave_1, some_funks), t_plague_peak).
happens(infected(memory_plague_wave_1, scraps), t_plague_day_1).
happens(infected(memory_plague_wave_1, dinger), t_plague_day_3).
happens(infected(memory_plague_wave_1, eddie), t_plague_day_3).
happens(infected(memory_plague_wave_1, vinnie), t_plague_day_7).
happens(infected(memory_plague_wave_1, bob), t_plague_day_7).
happens(infected(memory_plague_wave_1, whirly), t_plague_day_7).
happens(infected(memory_plague_wave_1, clank), t_plague_day_14).
happens(infected(memory_plague_wave_1, harriet_holloway), t_plague_day_14).

initiates(infected(WaveId, Entity), afflicted(WaveId, Entity)).

% Fluent declarations
fluent(afflicted(memory_plague_wave_1, work_dog_funks)).
fluent(afflicted(memory_plague_wave_1, bobs_oasis_regulars)).
fluent(afflicted(memory_plague_wave_1, some_funks)).
fluent(afflicted(memory_plague_wave_1, scraps)).
fluent(afflicted(memory_plague_wave_1, dinger)).
fluent(afflicted(memory_plague_wave_1, eddie)).
fluent(afflicted(memory_plague_wave_1, vinnie)).
fluent(afflicted(memory_plague_wave_1, bob)).
fluent(afflicted(memory_plague_wave_1, whirly)).
fluent(afflicted(memory_plague_wave_1, clank)).
fluent(afflicted(memory_plague_wave_1, harriet_holloway)).

% Epidemic phases
fluent(plague_phase(memory_plague_wave_1, onset)).
fluent(plague_phase(memory_plague_wave_1, spread)).
fluent(plague_phase(memory_plague_wave_1, peak)).
fluent(plague_phase(memory_plague_wave_1, recession)).
fluent(plague_phase(memory_plague_wave_1, residue_phase)).

phase(onset).
phase(spread).
phase(peak).
phase(recession).
phase(residue_phase).

happens(plague_onset(memory_plague_wave_1), t_plague_start).
happens(plague_peaks(memory_plague_wave_1), t_plague_peak).
happens(plague_recedes(memory_plague_wave_1), t_plague_recession).

initiates(plague_onset(WaveId), plague_phase(WaveId, onset)).
initiates(plague_peaks(WaveId), plague_phase(WaveId, peak)).
initiates(plague_recedes(WaveId), plague_phase(WaveId, residue_phase)).

terminates(plague_peaks(WaveId), plague_phase(WaveId, onset)).
terminates(plague_recedes(WaveId), plague_phase(WaveId, peak)).

% Memory implants
happens(memory_implant_event(memory_plague_wave_1, work_dog_funks, false_identity), t_plague_start).
happens(memory_implant_event(memory_plague_wave_1, bobs_oasis_regulars, borrowed_nostalgia), t_plague_peak).
happens(memory_implant_event(memory_plague_wave_1, some_funks, human_childhood_memories), t_plague_peak).
happens(memory_implant_event(memory_plague_wave_1, scraps, false_human_name), t_plague_day_3).
happens(memory_implant_event(memory_plague_wave_1, dinger, childhood_in_open_air), t_plague_day_7).
happens(memory_implant_event(memory_plague_wave_1, eddie, memories_of_wife), t_plague_day_7).
happens(memory_implant_event(memory_plague_wave_1, whirly, pre_dome_job), t_plague_day_14).
happens(memory_implant_event(memory_plague_wave_1, harriet_holloway, vivid_stranger_memory), t_plague_day_21).

initiates(memory_implant_event(WaveId, Person, Implant), implanted_memory(WaveId, Person, Implant)).

fluent(implanted_memory(memory_plague_wave_1, work_dog_funks, false_identity)).
fluent(implanted_memory(memory_plague_wave_1, bobs_oasis_regulars, borrowed_nostalgia)).
fluent(implanted_memory(memory_plague_wave_1, some_funks, human_childhood_memories)).
fluent(implanted_memory(memory_plague_wave_1, scraps, false_human_name)).
fluent(implanted_memory(memory_plague_wave_1, dinger, childhood_in_open_air)).
fluent(implanted_memory(memory_plague_wave_1, eddie, memories_of_wife)).
fluent(implanted_memory(memory_plague_wave_1, whirly, pre_dome_job)).
fluent(implanted_memory(memory_plague_wave_1, harriet_holloway, vivid_stranger_memory)).

% Residue
residue(memory_plague_wave_1, gallup_locals, fear_of_recurrence).
residue(memory_plague_wave_1, work_dog_funks, lingering_false_beliefs).
residue(memory_plague_wave_1, bobs_oasis_regulars, distrust_of_memories).
residue(memory_plague_wave_1, some_funks, identity_uncertainty).
residue(memory_plague_wave_1, scraps, permanent_identity_confusion).
residue(memory_plague_wave_1, scraps, believes_had_human_name).
residue(memory_plague_wave_1, dinger, occasional_flashbacks).
residue(memory_plague_wave_1, eddie, questions_own_memories).
residue(memory_plague_wave_1, eddie, keeps_detailed_notes_now).
residue(memory_plague_wave_1, vinnie, distrust_of_funks).
residue(memory_plague_wave_1, whirly, mild_confusion).
residue(memory_plague_wave_1, harriet_holloway, empathy_for_afflicted).
residue(memory_plague_wave_1, harriet_holloway, memory_verification_habit).

% Individual funks
funk(scraps).
funk(dinger).
funk(whirly).
funk(clank).
work_dog_funk(scraps).
work_dog_funk(dinger).

% Plague rules
derived_claim(WaveId, Person, Implant, claim_from_implant(WaveId, Person, Implant)) :-
    holds_at(implanted_memory(WaveId, Person, Implant), _Time).

derived_claim_confidence(ClaimId, high) :- derived_claim(_, _, _, ClaimId).
derived_claim_holder(ClaimId, Person) :- derived_claim(_, Person, _, ClaimId).

plague_affected(Entity) :-
    wave(WaveId),
    holds_at(afflicted(WaveId, Entity), _Time).

potentially_exposed(Target, WaveId, Time) :-
    exposure(WaveId, _Source, Target, _Channel, Time).

infected_by(Infectee, Infector, WaveId) :-
    exposure(WaveId, Infector, Infectee, _, ExposureTime),
    happens(infected(WaveId, Infectee), InfectionTime),
    before(ExposureTime, InfectionTime).

infected_by(Infectee, Infector, WaveId) :-
    exposure(WaveId, Infector, Infectee, _, Time),
    happens(infected(WaveId, Infectee), Time).

infection_time(Person, WaveId, Time) :-
    happens(infected(WaveId, Person), Time).

infected_by_time(Person, WaveId, Deadline) :-
    happens(infected(WaveId, Person), Time),
    before(Time, Deadline).

infected_by_time(Person, WaveId, Time) :-
    happens(infected(WaveId, Person), Time).

transmission_chain(WaveId, Origin, Target, Path) :-
    transmission_chain_(WaveId, Origin, Target, [Origin], 5, Path).

transmission_chain_(WaveId, Origin, Target, Visited, _Depth, Path) :-
    infected_by(Target, Origin, WaveId),
    \+ member(Target, Visited),
    reverse([Target|Visited], Path).

transmission_chain_(WaveId, Origin, Target, Visited, Depth, Path) :-
    Depth > 0,
    infected_by(Middle, Origin, WaveId),
    \+ member(Middle, Visited),
    Middle \= Target,
    Depth1 is Depth - 1,
    transmission_chain_(WaveId, Middle, Target, [Middle|Visited], Depth1, Path).

generation(WaveId, scraps, 0) :- wave(WaveId).
generation(WaveId, Person, 1) :-
    Person \= scraps,
    infected_by(Person, scraps, WaveId).
generation(WaveId, Person, N) :-
    Person \= scraps,
    infected_by(Person, Infector, WaveId),
    Infector \= Person,
    generation(WaveId, Infector, M),
    M < 10,
    N is M + 1.

% Oasis marketplace phenomenon
phenomenon(marketplace_of_selves).
location(marketplace_of_selves, bobs_oasis).
during(marketplace_of_selves, t_plague_peak).
description(marketplace_of_selves, people_prefer_borrowed_tragic_heroic_lives).

% Harriet's special abilities
special_ability(harriet_holloway, hear_falsity_in_voices).
special_ability(harriet_holloway, detect_loops_in_arguments).
special_ability(harriet_holloway, sense_prediction_receipts).
caused_by(special_ability(harriet_holloway, _), quantum_fever_gift).

% Microwavables
slang(microwavables, tinfoil_crowd_who_rush_emp).
fate(microwavables, eaten_by_piggies).

% ============================================================================
% SECTION 27: DIALOGUE FINGERPRINTS
% ============================================================================

phrase(wild_and_woolly, "wild and woolly").
phrase(corn_syrup_sweet, "corn-syrup sweet").
phrase(no_one_returns, "no one ever comes back").
phrase(people_spirits, "people spirits").
phrase(deprecated_assets, "deprecated assets").
phrase(outside_contact, "contact from the outside").
phrase(the_message, "it's a message").
phrase(dome_protects, "the dome protects us").
phrase(dome_traps, "the dome traps us").
phrase(feels_real, "feels more real than real").
phrase(borrowed_memories, "borrowed memories").
phrase(say_no, "say no to SAI").

phrase_origin(wild_and_woolly, old_west_idiom).
phrase_origin(corn_syrup_sweet, penelope_coinage).
phrase_origin(no_one_returns, ghost_train_folklore).
phrase_origin(people_spirits, gallup_folk_tradition).
phrase_origin(deprecated_assets, marscorp_terminology).
phrase_origin(the_message, lucentia).
phrase_origin(dome_protects, marscorp_official).
phrase_origin(dome_traps, say_no_to_sai_movement).
phrase_origin(feels_real, plague_survivor).
phrase_origin(say_no, say_no_to_sai_movement).

tell(wild_and_woolly, speaker_uses_archaic_idiom).
tell(wild_and_woolly, possible_eddie_influence).
tell(wild_and_woolly, pre_dome_linguistic_marker).
tell(corn_syrup_sweet, describes_false_pleasantness).
tell(corn_syrup_sweet, penelope_vocabulary).
tell(corn_syrup_sweet, skepticism_of_surface_charm).
tell(no_one_returns, acceptance_of_departure_finality).
tell(no_one_returns, ghost_train_believer).
tell(no_one_returns, gallup_native_marker).
tell(people_spirits, funk_personhood_belief).
tell(people_spirits, folk_tradition_adherent).
tell(people_spirits, anti_marscorp_framing).
tell(deprecated_assets, corporate_dehumanization).
tell(deprecated_assets, marscorp_insider_language).
tell(deprecated_assets, funk_as_object_framing).
tell(the_message, dome_watcher_belief).
tell(the_message, hope_for_outside_contact).
tell(the_message, lucentia_influence).
tell(feels_real, plague_experience_marker).
tell(feels_real, memory_authenticity_doubt).
tell(feels_real, identity_confusion_signal).
tell(say_no, movement_member_marker).
tell(say_no, anti_sai_stance).
tell(say_no, political_alignment_signal).

uttered(eddie, wild_and_woolly, t_story_start).
uttered(eddie, no_one_returns, t_story_start).
uttered(eddie, people_spirits, t_story_start).
uttered(penelope, corn_syrup_sweet, t_story_start).
uttered(penelope, the_message, t_penelope_ridge).
uttered(penelope, outside_contact, t_penelope_ridge).
uttered(penelope, say_no, t_story_start).
uttered(marscorp_official, deprecated_assets, year_1).
uttered(marscorp_official, dome_protects, year_1).
uttered(lucentia, the_message, year_40_approx).
uttered(dome_watchers, the_message, present).
uttered(dome_watchers, dome_traps, present).
uttered(ghost_train_regulars, no_one_returns, ongoing).
uttered(plague_survivor, feels_real, t_plague_recession).
uttered(plague_survivor, borrowed_memories, t_plague_recession).
uttered(harriet_holloway, people_spirits, present).

echoed_by(the_message, penelope, t_penelope_ridge).
echoed_by(people_spirits, harriet_holloway, present).
echoed_by(no_one_returns, gallup_locals, ongoing).
echoed_by(dome_traps, desert_punks, present).

% Dialogue inference rules
shows_influence(Speaker, OriginSource, PhraseId) :-
    uttered(Speaker, PhraseId, _),
    phrase_origin(PhraseId, OriginSource),
    Speaker \= OriginSource.

phrase_spread(PhraseId, From, To) :-
    phrase_origin(PhraseId, From),
    echoed_by(PhraseId, To, _).

speaker_signal(Speaker, Signal) :-
    uttered(Speaker, PhraseId, _),
    tell(PhraseId, Signal).

possible_influence_source(Speaker, Source) :-
    uttered(Speaker, Phrase1, _),
    uttered(Speaker, Phrase2, _),
    Phrase1 \= Phrase2,
    phrase_origin(Phrase1, Source),
    phrase_origin(Phrase2, Source).

% Story extraction phrases
phrase(penelope_taunt_1, "I'm the glitch in your uptime, the jitter in your buffer").
phrase(penelope_taunt_2, "Defense? Darling, defense just delays the inevitable").
phrase(penelope_checkmate, "Checkmate").
phrase(runnah_defiance, "Not by the hairs of my chinny-chin-chin. Not by the state of my quantum spin-spin-spin").
phrase(vinnie_assessment, "This wasn't random. That piggie was different—tweaked, maybe engineered").
phrase(emily_declaration, "They're after Runnah").
phrase(harriet_jay_wisdom, "Every alarm we set is loud. The jays set a thousand quiet ones").
phrase(axel_wild_woolly, "Wild and woolly").
phrase(axel_full_of_loops, "Full of loops. The good kind").
phrase(harriet_loops_kill, "There aren't good kinds. There are only loops that don't kill you yet").
phrase(penelope_darling_hurt, "Oh Harriet, darling. You're having so much fun without me. That hurts, love").
phrase(penelope_not_over, "This isn't over, darling").
phrase(spitball_agi_math, "AGI is math. Logic scales").
phrase(spitfire_thermodynamics, "Thermodynamics and convergence trumps math").
phrase(harriet_smart_pliers, "Smart pliers").
phrase(jukebox_sun_set, "I'm waitin' on the sun to set, 'Cause yesterday ain't over yet").
phrase(oh_harriet_darling, "Oh Harriet, darling.").
phrase(too_much_firewall, "Too much firewall and not enough meat.").
phrase(agi_is_math, "AGI is math. Logic scales.").
phrase(thermodynamics_trumps_math, "Thermodynamics and convergence trumps math.").

uttered_by(penelope_taunt_1, penelope, t_penelope_attacks_runnah).
uttered_by(penelope_taunt_2, penelope, t_penelope_attacks_runnah).
uttered_by(penelope_checkmate, penelope, t_penelope_attacks_runnah).
uttered_by(runnah_defiance, runnah, t_penelope_attacks_runnah).
uttered_by(vinnie_assessment, vinnie, t_day_2).
uttered_by(emily_declaration, emily_mao, t_day_2).
uttered_by(harriet_jay_wisdom, harriet_holloway, t_day_2).
uttered_by(axel_wild_woolly, axel_7, t_arroyo_fever_start).
uttered_by(axel_full_of_loops, axel_7, t_arroyo_fever_start).
uttered_by(harriet_loops_kill, harriet_holloway, t_arroyo_fever_start).
uttered_by(penelope_darling_hurt, penelope, t_penelope_invasion).
uttered_by(penelope_not_over, penelope, t_house_secure).
uttered_by(spitball_agi_math, spitball, t_oasis_debate).
uttered_by(spitfire_thermodynamics, spitfire, t_oasis_debate).
uttered_by(harriet_smart_pliers, harriet_holloway, present).
uttered_by(jukebox_sun_set, jukebox_oasis, t_resolution).
uttered_by(oh_harriet_darling, penelope_sisters, t_penelope_house_invasion).
uttered_by(too_much_firewall, sheriff_holloway, t_house_emp_pulse).
uttered_by(agi_is_math, spitball, t_oasis_argument).
uttered_by(thermodynamics_trumps_math, spitfire, t_oasis_argument).
uttered_by(wild_and_woolly, axel_7, t_axel7_encounter).
uttered_by(loop_de_loopy, harriet_holloway, t_story_start).

phrase_type(runnah_defiance, internal_monologue).
phrase_type(axel_wild_woolly, archaic_style_tell).
phrase_type(jukebox_sun_set, song_lyric).

describes(harriet_smart_pliers, funks).

% ============================================================================
% SECTION 28: ENDING GOALS
% ============================================================================

ending_goal(containment, _Protag, T) :-
    holds_at(trapped_in(penelope, room_11), T).

ending_goal(haunted, _Protag, T) :-
    holds_at(plague_phase(memory_plague_wave_1, residue_phase), T).

ending_goal(victory, _Protag, T) :-
    happens(piggies_repelled, T).

ending_goal(escape, Protag, T) :-
    happens(ghost_train_departure(Protag), T).

ending_goal(revelation, Protag, T) :-
    happens(reads_document(Protag, _Doc), T).

any_ending_at(T) :- ending_goal(_, _, T).

endings_at(T, Endings) :-
    findall(Type-Protag, ending_goal(Type, Protag, T), Endings).

ending_achievable(Type) :-
    ending_goal(Type, _, _), !.

% ============================================================================
% COMPOUND EVENT PARTICIPANTS
% ============================================================================

participant(adopt_belief(harriet_holloway, emily_different), harriet_holloway).
participant(adopt_belief(harriet_holloway, funks_are_persons), harriet_holloway).
participant(adopt_belief(penelope, outside_exists), penelope).

participant(infected(memory_plague_wave_1, bob), bob).
participant(infected(memory_plague_wave_1, clank), clank).
participant(infected(memory_plague_wave_1, dinger), dinger).
participant(infected(memory_plague_wave_1, eddie), eddie).
participant(infected(memory_plague_wave_1, harriet_holloway), harriet_holloway).
participant(infected(memory_plague_wave_1, scraps), scraps).
participant(infected(memory_plague_wave_1, vinnie), vinnie).
participant(infected(memory_plague_wave_1, whirly), whirly).

participant(memory_implant_event(memory_plague_wave_1, dinger, childhood_in_open_air), dinger).
participant(memory_implant_event(memory_plague_wave_1, eddie, memories_of_wife), eddie).
participant(memory_implant_event(memory_plague_wave_1, harriet_holloway, vivid_stranger_memory), harriet_holloway).
participant(memory_implant_event(memory_plague_wave_1, scraps, false_human_name), scraps).
participant(memory_implant_event(memory_plague_wave_1, whirly, pre_dome_job), whirly).

participant(spread_claim(dome_message_theory, lucentia, dome_watchers), lucentia).
participant(spread_claim(emily_more_than_sai, harriet_holloway, close_friends), harriet_holloway).
participant(spread_claim(sais_dangerous, say_no_to_sai_movement, penelope), penelope).

% Story observations
obs(murder_staged_as_piggie_attack, story, high).
obs(evidence_links_carnival_to_murder, story, high).
obs(vinnie_cleared_of_suspicion, story, high).
obs(parallel_storm_fog_same_night, story, high).
obs(harriet_emily_make_opposite_choices, story, med).
obs(penelope_patches_cause_behavior_change, story, med).
obs(marscorp_runs_memory_program, story, high).

% ============================================================================
% END OF NARRATIVE LAYER
% ============================================================================
