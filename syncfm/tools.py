#-*- coding: utf-8 -*-
# 
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses

import logging

class ColorFormatter(logging.Formatter):
    """Implements basic colored output using ANSI escape codes."""
    
    BLACK = '\033[0;30m%s\033[0m'
    RED = '\033[0;31m%s\033[0m'
    GREY = '\033[0;37m%s\033[0m'
    RED_UNDERLINE = '\033[4;31m%s\033[0m'
    
    def __init__(self, fmt='[%(levelname)s] %(name)s: %(message)s'):
        logging.Formatter.__init__(self, fmt)
        
    def format(self, record):
        if record.levelname == 'DEBUG':
            record.levelname = self.BLACK % record.levelname
        elif record.levelname == 'INFO':
            record.levelname = self.GREY % record.levelname
        elif record.levelname in ('WARN', 'WARNING'):
            record.levelname = self.RED % record.levelname
        elif record.levelname in ('ERROR', 'CRITICAL', 'FATAL'):
            record.levelname = self.RED_UNDERLINE % record.levelname
        return logging.Formatter.format(self, record)
