# vim: set encoding=utf-8
import unittest

from selenium.webdriver.support.ui import WebDriverWait

from regulations.uitests.base_test import BaseTest


class DefinitionTest(BaseTest, unittest.TestCase):

    job_name = 'Definitions test'

    def test_definition(self):
        self.driver.set_window_size(1024, 600)
        self.driver.get(self.test_url + '/1005-1/2012-12121')
        html = self.driver.find_element_by_tag_name('html')
        WebDriverWait(self.driver, 30).until(
            lambda driver: 'selenium-start' in html.get_attribute('class'))
        definition_link = self.driver.find_element_by_xpath(
            '//*[@id="1005-1-a"]//a')
        # term link should have correct data attr
        self.assertTrue(
            '1005-2-a-1' in definition_link.get_attribute('data-definition'))

        definition_link.click()

        # term link should get active class
        self.assertTrue('active' in definition_link.get_attribute('class'))

        definition = self.driver.find_element_by_xpath('//*[@id="1005-2-a-1"]')
        definition_close_button = self.driver.find_element_by_xpath(
            '//*[@id="1005-2-a-1"]/div[1]/h4/a')

        # definition should appear in sidebar
        self.assertTrue(len(definition.text) > 20)
        definition_term = self.driver.find_element_by_xpath(
            '//*[@id="1005-2-a-1"]/div[3]/p/dfn')
        self.assertTrue(u'\u201cvoided tosser\u201d' in definition_term.text)

        definition_close_button.click()
        # definition should close
        self.assertFalse('active' in definition_link.get_attribute('class'))

        definition_link.click()

        # continue link should load full def
        definition_cont_link = self.driver.find_element_by_xpath(
            '//*[@id="1005-2-a-1"]/div[3]/a[1]')
        definition_cont_link.click()
        WebDriverWait(self.driver, 30).until(
            lambda driver: driver.find_element_by_xpath('//*[@id="1005-2"]'))

        # test definition scope notifications
        toc_toggle = self.driver.find_element_by_xpath('//*[@id="panel-link"]')
        toc_toggle.click()

        toc_1005_3 = self.driver.find_element_by_xpath(
            '//*[@id="toc"]/ol/li[3]/a')
        toc_1005_3.click()

        # close toc
        toc_toggle.click()

        # load 1005.3, open definition
        new_definition_link = self.driver.find_element_by_xpath(
            '//*[@id="1005-3-a"]//a[1]')
        new_definition_link.click()
        self.driver.find_element_by_xpath('//*[@id="1005-2-b-1"]')

        # navigate back to 1005.1
        toc_toggle.click()
        self.driver.find_element_by_xpath('//*[@id="toc"]/ol/li[1]/a').click()

        # make sure that the scope notice displays
        self.driver.find_element_by_xpath('//*[@id="1005-2-b-1"]/div[2]/div')

        # go to 1005-1-a
        toc_toggle.click()
        WebDriverWait(self.driver, 10)
        headers_seen = set()
        script = "window.scrollTo(0, {}/5*document.body.scrollHeight);"
        for i in range(6):
            self.driver.execute_script(script.format(i))
            wayfinding_header = self.driver.find_element_by_xpath(
                '//*[@id="active-title"]/em')
            headers_seen.add(wayfinding_header.text)
        self.assertIn(u'§1005.1', headers_seen)
        self.assertIn(u'§1005.1(a)', headers_seen)

        # (b) _may_ be seen, depending on fiddly bits in the driver
        self.assertIn(len(headers_seen), (2, 3))
        if len(headers_seen) == 3:
            self.assertIn(u'§1005.1(b)', headers_seen)

        print "".join(c for c in self.driver.find_element_by_xpath(
            '//*[@id="1005-2-b-1"]/div[2]/div').get_attribute(
                    'innerHTML') if ord(c) < 128)
        definition_update_link = self.driver.find_element_by_xpath(
            '//*[@id="1005-2-b-1"]/div[2]/div/a')
        definition_text = self.driver.find_element_by_xpath(
            '//*[@id="1005-2-b-1"]/div[3]')

        # make sure text is grayed out
        self.assertTrue('inactive' in definition_text.get_attribute('class'))

        # load in scope definition
        definition_update_link.click()
        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.find_element_by_xpath(
                '//*[@id="1005-2-a-1"]'))
