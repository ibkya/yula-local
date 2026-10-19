import copy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from core import Engine, Screen
from desktop import crop_window, tesseract_words

# Private screen captures stay outside the project (they show account details).
CAPTURES = Path(os.environ.get('YULA_CAPTURES', Path.home() / 'Desktop/yula-arsiv/test-captures'))


def word(text, x, y, w=.025):
    return dict(text=text, x=x, y=y, w=w, h=.012, confidence=1)


def favorites(index=2, moving=0):
    words = [word('yulaonline.com', .45, .02), word('YAĞMA', .3, .25),
             word('FAVORİLERİ', .35, .25), word('1-50', .25, .4),
             word('51-100', .29, .4), word(str(index), .29, .5),
             word('merkez', .32, .5), word('600', .49, .5), word('|', .51, .5),
             word('201', .53, .5), word('Git', .63, .5), word('Yağma', .66, .5)]
    if moving:
        words += [word('yolda', .56, .5), word(str(moving), .59, .5)]
    return words


def selection(amount=0, total=None, confirm_x=.7, cooldown=False):
    words = [word('yulaonline.com', .45, .02), word('ASKER', .3, .25),
             word('GÖNDER', .35, .25), word('GÖNDERİLECEK', .2, .6),
             word('Konum:', .5, .4), word('600', .56, .4), word('|', .59, .4),
             word('201', .61, .4), word('Okçu', .43, .65),
             word(str(amount), .43, .69), word('+100', .43, .72),
             word('Tamam', confirm_x, .8), word('Vazgeç', .6, .8)]
    if total is not None:
        words += [word(str(total), .2, .8), word('birlik', .23, .8)]
    if cooldown:
        words += [word('ganimet', .6, .55), word('alınmaz', .67, .55)]
    return words


class FlowTests(unittest.TestCase):
    def test_full_200_target_state_cycle(self):
        engine = Engine(1, 200)
        for index in range(1, 201):
            self.assertEqual(engine.step(Screen(favorites(index))).kind, 'click')
            self.assertIn('+100', engine.step(Screen(selection())).reason)
            self.assertEqual(engine.step(Screen(selection(100, 100))).kind, 'click')
            self.assertEqual(engine.state['next'], index)
            engine.step(Screen(favorites(index, moving=1)))
            self.assertEqual(engine.state['next'], index+1)
        self.assertEqual(engine.state['completed'], list(range(1, 201)))
        self.assertEqual(engine.step(Screen(favorites(200))).kind, 'done')

    def test_action_fingerprint_changes_with_destination_quantity_or_button(self):
        first = Screen(selection(100, 100)).fingerprint('Okçu')
        self.assertNotEqual(first, Screen(selection(0, None)).fingerprint('Okçu'))
        self.assertNotEqual(first, Screen(selection(100, 100, confirm_x=.3)).fingerprint('Okçu'))
        self.assertNotEqual(Screen(favorites(2)).fingerprint('Okçu'),
                            Screen(favorites(3)).fingerprint('Okçu'))

    def test_repeated_scroll_without_progress_stops(self):
        engine = Engine(8, 9)
        self.assertEqual(engine.step(Screen(favorites())).kind, 'scroll')
        self.assertEqual(engine.step(Screen(favorites())).kind, 'scroll')
        self.assertEqual(engine.step(Screen(favorites())).kind, 'stop')
        self.assertEqual(engine.state['completed'], [])

    def test_contradicting_adjacent_reads_never_click(self):
        words = favorites(2)
        words += [dict(w, y=w['y']+.08) for w in favorites(4)[5:]]
        engine = Engine(3, 5)
        for _ in range(3):
            self.assertEqual(engine.step(Screen(words)).kind, 'wait')

    def list_rows(self, reads, pitch=.045):
        words = favorites(1)[:5]  # domain, header, tabs
        for i, read in enumerate(reads):
            y = .5 + i * pitch
            words += [word('merkez', .32, y), word(str(600 + i), .49, y), word('|', .51, y),
                      word('201', .53, y), word('Git', .63, y), word('Yağma', .66, y)]
            if read is not None:
                words.append(word(str(read), .29, y))
        return words

    def test_missing_row_number_is_inferred_from_neighbours(self):
        rows = Screen(self.list_rows([7, None, 9, None, 11])).rows()
        self.assertEqual([(r['index'], r['coords'][0]) for r in rows],
                         [(7, 600), (8, 601), (9, 602), (10, 603), (11, 604)])

    def test_single_misread_is_outvoted(self):
        rows = Screen(self.list_rows([9, 10, 41, 12])).rows()
        self.assertEqual([r['index'] for r in rows], [9, 10, 11, 12])

    def test_no_majority_trusts_no_row(self):
        self.assertEqual(Screen(self.list_rows([9, 41, None])).rows(), [])

    def test_single_read_does_not_number_neighbours(self):
        rows = Screen(self.list_rows([None, 8, None])).rows()
        self.assertEqual([r['index'] for r in rows], [8])

    def test_unreadable_visible_target_nudges_twice_then_stops(self):
        words = self.list_rows([1, 2, 3, 4, 5])
        words.remove(next(w for w in words if w['text'] == 'Yağma' and abs(w['y'] - .59) < .001))
        self.assertEqual([r['index'] for r in Screen(words).rows()], [1, 2, 4, 5])
        engine = Engine(3, 4)
        kinds = [engine.step(Screen(words)).kind for _ in range(9)]
        self.assertEqual(kinds, ['wait', 'wait', 'scroll'] * 2 + ['wait', 'wait', 'stop'])
        self.assertEqual(engine.state['completed'], [])

    def test_moving_counter_survives_noise_and_glued_reads(self):
        noisy = favorites(2) + [word('yolda', .56, .5), word('yaar', .575, .5), word('1', .59, .5)]
        self.assertEqual(Screen(noisy).rows()[0]['moving'], 1)
        glued = favorites(2) + [word('yolda2', .56, .5)]
        self.assertEqual(Screen(glued).rows()[0]['moving'], 2)

    def test_misread_plus_button_is_not_quantity(self):
        words = selection(0) + [word('4100', .43, .72)]
        self.assertEqual(Screen(words).troop('Okçu')[0], 0)

    def test_delete_button_noise_is_not_coordinates(self):
        words = favorites(5) + [word('3', .2, .5), word('|', .205, .5), word('5', .21, .5)]
        self.assertEqual(Screen(words).rows()[0]['coords'], [600, 201])

    def test_bracketed_tab_is_clickable(self):
        words = favorites(60) + [word('[1-50]', .2, .4)]
        words = [w for w in words if w['text'] != '1-50']
        result = Engine(1, 2).step(Screen(words))
        self.assertIn('1-50', result.reason)

    def test_unreadable_edge_row_cannot_cause_unbounded_scroll(self):
        words = favorites(2) + [word('Yağma', .66, .6)]
        engine = Engine(3, 4)
        for _ in range(2):
            self.assertEqual(engine.step(Screen(words)).kind, 'scroll')
        self.assertEqual(engine.step(Screen(words)).kind, 'stop')

    def test_scroll_direction_and_target_after_progress(self):
        engine = Engine(8, 9)
        self.assertEqual(engine.step(Screen(favorites(2))).scroll, -1)
        self.assertEqual(engine.step(Screen(favorites(12))).scroll, 1)
        self.assertEqual(engine.step(Screen(favorites(8))).kind, 'click')
        self.assertEqual(engine.state['target']['index'], 8)

    def test_row_detection_under_affine_layout_changes(self):
        for scale in (.55, .75, 1, 1.1):
            words = [dict(w, x=w['x']*scale, y=w['y']*scale,
                          w=w['w']*scale, h=w['h']*scale) for w in favorites(8)]
            self.assertEqual(Screen(words).rows()[0]['index'], 8)

    def test_unreadable_zero_is_cleared_before_increment_and_200_stops(self):
        engine = self.open_target()
        words = [w for w in selection() if w['text'] != '0'] + [word('Temizle', .75, .6)]
        self.assertIn('sıfırla', engine.step(Screen(words)).reason)
        self.assertIn('+100', engine.step(Screen(words)).reason)
        self.assertEqual(engine.step(Screen(selection(200, 200))).kind, 'stop')

    def test_generic_captcha_mentions_are_not_a_modal(self):
        for text in ['kaydır', 'doğrulandı', 'CAPTCHA', 'robot', 'parçayı']:
            self.assertFalse(Screen(favorites() + [word(text, .3, .9)]).captcha)

    def test_wait_log_is_not_a_modal(self):
        words = favorites() + [word('İnsan', .3, .9), word('doğrulaması', .4, .9),
                               word('açık;', .5, .9), word('bekliyor', .6, .9)]
        self.assertFalse(Screen(words).captcha)

    def open_target(self):
        engine = Engine(2, 3)
        self.assertEqual(engine.step(Screen(favorites())).kind, 'click')
        return engine

    def test_success_advances_only_after_target_counter(self):
        engine = self.open_target()
        self.assertIn('+100', engine.step(Screen(selection())).reason)
        self.assertEqual(engine.step(Screen(selection(100, 100))).kind, 'click')
        self.assertEqual(engine.state['phase'], 'pending')
        engine.step(Screen(favorites(moving=1)))
        self.assertEqual(engine.state['next'], 3)
        self.assertEqual(engine.state['completed'], [2])

    def test_captcha_priority_over_underlying_game(self):
        engine = self.open_target()
        overlay = selection() + [word('İNSAN', .3, .3), word('DOĞRULAMASI', .4, .3)]
        for _ in range(10):
            self.assertEqual(engine.step(Screen(overlay)).kind, 'wait')
        self.assertEqual(engine.state['phase'], 'select')
        for _ in range(2):
            self.assertEqual(engine.step(Screen(selection())).kind, 'wait')
        self.assertIn('+100', engine.step(Screen(selection())).reason)

    def test_captcha_does_not_double_increment_selected_troop(self):
        engine = self.open_target()
        engine.step(Screen(selection()))
        engine.step(Screen(selection(100, 100) + [word('İNSAN', .3, .3), word('DOĞRULAMASI', .4, .3)]))
        for _ in range(2):
            engine.step(Screen(selection(100, 100)))
        result = engine.step(Screen(selection(100, 100)))
        self.assertIn('gönder', result.reason)
        self.assertNotIn('+100', result.reason)

    def test_pending_after_captcha_resumes_when_verified(self):
        engine = self.open_target()
        engine.step(Screen(selection(100, 100)))
        engine.step(Screen(favorites() + [word('İNSAN', .3, .3), word('DOĞRULAMASI', .4, .3)]))
        for _ in range(3):
            engine.step(Screen(favorites(moving=1)))
        self.assertEqual(engine.state['next'], 3)

    def test_ambiguous_submit_never_retries_even_after_restart(self):
        engine = self.open_target()
        engine.step(Screen(selection(100, 100)))
        resumed = Engine(state=copy.deepcopy(engine.state))
        kinds = [resumed.step(Screen(selection(100, 100))).kind for _ in range(4)]
        self.assertEqual(kinds, ['wait', 'wait', 'wait', 'stop'])  # never 'click'
        self.assertEqual(resumed.state['next'], 2)

    def test_unrelated_toast_is_not_confirmation(self):
        engine = self.open_target()
        engine.step(Screen(selection(100, 100)))
        screen = favorites() + [word('Yağma yola çıktı', .3, .1)]
        kinds = [engine.step(Screen(screen)).kind for _ in range(4)]
        self.assertEqual(kinds, ['wait', 'wait', 'wait', 'stop'])
        self.assertEqual(engine.state['completed'], [])

    def test_late_counter_after_submit_is_accepted(self):
        engine = self.open_target()
        engine.step(Screen(selection(100, 100)))
        self.assertEqual(engine.step(Screen(selection(100, 100))).kind, 'wait')
        self.assertEqual(engine.step(Screen(favorites())).kind, 'wait')
        engine.step(Screen(favorites(moving=1)))
        self.assertEqual(engine.state['completed'], [2])

    def test_shifted_confirmation_uses_current_position(self):
        engine = self.open_target()
        result = engine.step(Screen(selection(100, 100, confirm_x=.3)))
        self.assertAlmostEqual(result.x, .3125)

    def test_low_confidence_troop_label_above_single_plus_is_used(self):
        words = selection()
        next(w for w in words if w['text'] == 'Okçu')['confidence'] = .3
        self.assertEqual(Screen(words).troop('Okçu')[0], 0)
        # Without a +100 directly below, a weak label is not trusted.
        stray = [w for w in words if w['text'] != '+100']
        self.assertIsNone(Screen(stray).troop('Okçu'))

    def test_low_confidence_raid_button_needs_git_beside_it(self):
        words = favorites(1)
        next(w for w in words if w['text'] == 'Yağma')['confidence'] = .3
        self.assertEqual([r['index'] for r in Screen(words).rows()], [1])
        alone = [w for w in words if w['text'] != 'Git']
        self.assertEqual(Screen(alone).rows(), [])

    def test_unreadable_troop_retries_before_stopping(self):
        engine = self.open_target()
        missing = [w for w in selection() if w['text'] != 'Okçu']
        self.assertEqual(engine.step(Screen(missing)).kind, 'wait')
        self.assertIn('+100', engine.step(Screen(selection())).reason)
        engine = self.open_target()
        for _ in range(2):
            self.assertEqual(engine.step(Screen(missing)).kind, 'wait')
        self.assertEqual(engine.step(Screen(missing)).kind, 'stop')

    def test_sidebar_counter_above_birlik_menu_is_not_total(self):
        words = selection(100, 100) + [word('636.816', .03, .18), word('816', .03, .2),
                                       word('BİRLİK', .03, .28)]
        self.assertEqual(Screen(words).total(), 100)

    def test_wrong_total_stops(self):
        engine = self.open_target()
        self.assertEqual(engine.step(Screen(selection(100, 200))).kind, 'stop')

    def test_wrong_destination_stops(self):
        engine = self.open_target()
        words = selection(100, 100)
        next(w for w in words if w['text'] == '600')['text'] = '601'
        self.assertEqual(engine.step(Screen(words)).kind, 'stop')

    def test_cooldown_cancels_and_skips_after_list_return(self):
        engine = self.open_target()
        self.assertIn('atla', engine.step(Screen(selection(100, 100, cooldown=True))).reason)
        self.assertEqual(engine.state['next'], 2)
        engine.step(Screen(favorites()))
        self.assertEqual(engine.state['skipped'], [2])
        self.assertEqual(engine.state['next'], 3)

    def test_missing_domain_never_clicks(self):
        engine = Engine(2, 3)
        words = favorites()[1:]
        self.assertEqual(engine.step(Screen(words)).kind, 'wait')

    def test_missing_row_scrolls_without_advancing(self):
        engine = Engine(8, 9)
        action = engine.step(Screen(favorites()))
        self.assertEqual(action.kind, 'scroll')
        self.assertEqual(engine.state['next'], 8)

    def test_group_transition(self):
        engine = Engine(51, 52)
        result = engine.step(Screen(favorites()))
        self.assertEqual(result.kind, 'click')
        self.assertIn('51-100', result.reason)

    def test_unknown_during_captcha_recovery_resets_stability(self):
        engine = self.open_target()
        engine.step(Screen([word('İNSAN', .3, .3), word('DOĞRULAMASI', .4, .3)]))
        engine.step(Screen(selection()))
        engine.step(Screen([]))
        self.assertEqual(engine.step(Screen(selection())).kind, 'wait')
        self.assertEqual(engine.step(Screen(selection())).kind, 'wait')
        self.assertEqual(engine.step(Screen(selection())).kind, 'click')


class LocalCaptureTests(unittest.TestCase):
    def test_resized_and_scrolled_recordings(self):
        root = CAPTURES
        expected = {'list': list(range(1, 8)), 'scrolled': list(range(11, 18))}
        for prefix, indices in expected.items():
            for width in (1366, 1920, 2560):
                path = root / f'{prefix}-{width}.json'
                if not path.exists():
                    self.skipTest('Özel ekran kayıtları bu makinede yok.')
                screen = Screen(json.loads(path.read_text()))
                self.assertEqual([r['index'] for r in screen.rows()], indices, (prefix, width))

    def test_real_captures_when_available(self):
        root = CAPTURES
        if not (root / 'favorites-2x.json').exists():
            self.skipTest('Yerel ekran kayıtları paylaşılmaz; bu makinede mevcut değil.')
        favorites_screen = Screen(json.loads((root / 'favorites-2x.json').read_text()))
        self.assertEqual([r['index'] for r in favorites_screen.rows()], list(range(1, 8)))
        engine = Engine(2, 3)
        self.assertEqual(engine.step(favorites_screen).kind, 'click')
        for name in ['selection', 'selected']:
            screen = Screen(json.loads((root / f'{name}.json').read_text()))
            self.assertEqual(engine.step(screen).kind, 'click')
        captcha = Screen(json.loads((root / 'captcha.json').read_text()))
        self.assertEqual(engine.step(captcha).kind, 'wait')


class PanelTests(unittest.TestCase):
    def test_tour_choice(self):
        from panel import tour_choice
        self.assertEqual(tour_choice(None), 'new')
        self.assertEqual(tour_choice({'next': 201, 'end': 200, 'phase': 'list'}), 'new')
        self.assertEqual(tour_choice({'next': 7, 'end': 200, 'phase': 'list'}), 'resume')
        self.assertEqual(tour_choice({'next': 7, 'end': 200, 'phase': 'pending'}), 'pending')

    def test_check_summary(self):
        from panel import check_summary
        output = 'Chrome ön planda değil; bekliyor.\n' + json.dumps(
            {'screen': 'favorites', 'captcha': False, 'target': None, 'total': None,
             'rows': [{'index': 1, 'coords': [599, 188], 'moving': 0},
                      {'index': 2, 'coords': [600, 201], 'moving': 0}]}, indent=2)
        ok, text = check_summary(output + '\nOkunan ekran kaydedildi.')
        self.assertTrue(ok)
        self.assertIn('1–2', text)
        self.assertFalse(check_summary(json.dumps({'screen': 'unknown', 'captcha': False}))[0])
        self.assertIn('CAPTCHA', check_summary(json.dumps({'screen': 'captcha', 'captcha': True}))[1])
        self.assertFalse(check_summary('Güvenli duruş: hata')[0])


class PlatformTests(unittest.TestCase):
    def test_window_crop_excludes_terminal_at_retina_scale(self):
        from PIL import Image
        desktop = Image.new('RGB', (2000, 1600), 'red')
        desktop.paste('blue', (200, 100, 1800, 1500))
        cropped = crop_window(desktop, {'x': 100, 'y': 50, 'width': 800, 'height': 700}, (1000, 800))
        self.assertEqual(cropped.size, (1600, 1400))
        self.assertEqual(cropped.getpixel((0, 0)), (0, 0, 255))

    def test_partial_offscreen_window_stops(self):
        from PIL import Image
        with self.assertRaises(RuntimeError):
            crop_window(Image.new('RGB', (1000, 800)),
                        {'x': -10, 'y': 0, 'width': 800, 'height': 700}, (1000, 800))

    def test_tesseract_output_maps_confidence_and_coordinates(self):
        words = tesseract_words({'text': ['', 'Yağma'], 'conf': ['-1', '92.5'],
                                 'left': [0, 100], 'top': [0, 200],
                                 'width': [0, 50], 'height': [0, 20]}, 1000, 800)
        self.assertEqual(len(words), 1)
        self.assertEqual(words[0]['confidence'], .925)
        self.assertEqual(words[0]['x'], .1)
        self.assertEqual(words[0]['y'], .25)


if __name__ == '__main__':
    unittest.main()
